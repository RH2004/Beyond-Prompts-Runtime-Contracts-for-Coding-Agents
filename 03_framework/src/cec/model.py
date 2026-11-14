"""LiteLLM model with the condition's tool set and per-call usage/latency/retry capture (decision 0002-A3)."""

import json
import logging
import time

import litellm
from jinja2 import StrictUndefined, Template

from minisweagent.exceptions import FormatError
from minisweagent.models import GLOBAL_MODEL_STATS
from minisweagent.models.litellm_model import LitellmModel, LitellmModelConfig
from minisweagent.models.utils.actions_toolcall import BASH_TOOL
from minisweagent.models.utils.retry import retry

from .edit_tool import EDIT_TOOL_NAMES, EDIT_TOOLS, TOOL_ALIASES

logger = logging.getLogger("cec.model")


class CreditsExhausted(Exception):
    """Provider refused the request for lack of credits. Not retryable; the run is an infrastructure failure."""


def _is_credit_error(e: Exception) -> bool:
    text = str(e).lower()
    return getattr(e, "status_code", None) == 402 or "requires more credits" in text or "insufficient credits" in text

LOOKUP_TOOL = {
    "type": "function",
    "function": {
        "name": "lookup_rules",
        "description": "Look up the engineering rules that apply to this task, by keyword or file path.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Keyword, rule id, or repository path"}},
            "required": ["query"],
        },
    },
}


def tools_for(condition) -> list[dict]:
    tools = [BASH_TOOL, *EDIT_TOOLS]
    if condition.structured_retrieval:
        tools.append(LOOKUP_TOOL)
    return tools


def extract_usage(response) -> dict:
    """Token usage as reported by the provider. Missing fields stay None; never estimated (decision 0002-A3)."""
    usage = getattr(response, "usage", None)
    get = (lambda k: getattr(usage, k, None)) if usage is not None else (lambda k: None)
    rec = {
        "input_tokens": get("prompt_tokens"),
        "output_tokens": get("completion_tokens"),
        "cache_read_input_tokens": get("cache_read_input_tokens") or getattr(get("prompt_tokens_details"), "cached_tokens", None),
        "cache_creation_input_tokens": get("cache_creation_input_tokens"),
    }
    rec["usage_missing"] = rec["input_tokens"] is None or rec["output_tokens"] is None
    return rec


def parse_actions(tool_calls, tool_names: set[str], format_error_template: str, finish_reason=None) -> list[dict]:
    def fail(msg, has_calls):
        msg = (f"{msg} Available tools: {', '.join(sorted(tool_names))}. "
               "Repository files can only be changed with the view, create and str_replace tools.")
        raise FormatError(
            {
                "role": "user",
                "content": Template(format_error_template, undefined=StrictUndefined).render(
                    error=msg, actions=[], has_tool_calls=has_calls, finish_reason=finish_reason
                ),
                "extra": {"interrupt_type": "FormatError"},
            }
        )

    if not tool_calls:
        fail("No tool calls found in the response. Every response MUST include at least one tool call.", False)
    actions = []
    for tc in tool_calls:
        try:
            args = json.loads(tc.function.arguments)
        except Exception as e:
            fail(f"Error parsing tool call arguments: {e}.", True)
        if TOOL_ALIASES.get(tc.function.name, tc.function.name) not in tool_names:
            fail(f"Unknown tool '{tc.function.name}'.", True)
        if not isinstance(args, dict):
            fail("Tool arguments must be an object.", True)
        if TOOL_ALIASES.get(tc.function.name, tc.function.name) == "bash" and "command" not in args:
            fail("Missing 'command' argument in bash tool call.", True)
        name = TOOL_ALIASES.get(tc.function.name, tc.function.name)
        if name == "bash":
            actions.append({"tool": "bash", "args": args, "command": args.get("command", ""), "tool_call_id": tc.id})
        elif name in EDIT_TOOL_NAMES:
            actions.append({"tool": "edit", "args": {"command": name, **args}, "command": "", "tool_call_id": tc.id,
                            "tool_name_called": tc.function.name})
        else:
            actions.append({"tool": name, "args": args, "command": "", "tool_call_id": tc.id})
    return actions


class ContractModel(LitellmModel):
    def __init__(self, *, condition, **kwargs):
        super().__init__(config_class=LitellmModelConfig, **kwargs)
        self.tools = tools_for(condition)
        self.tool_names = {t["function"]["name"] for t in self.tools}

    abort_exceptions = LitellmModel.abort_exceptions + [CreditsExhausted]

    def _query(self, messages, **kwargs):
        try:
            return litellm.completion(
                model=self.config.model_name, messages=messages, tools=self.tools, **(self.config.model_kwargs | kwargs)
            )
        except Exception as e:  # noqa: BLE001 - classify, then re-raise unchanged
            if _is_credit_error(e):
                raise CreditsExhausted(str(e)[:500]) from e
            raise

    def _calculate_cost(self, response) -> dict:
        """Provider-reported cost (OpenRouter usage.cost) first, then LiteLLM's price map.
        If neither is available the cost is recorded as missing (cost_missing=True) and counted as 0 for limits;
        it is never estimated (decision 0002-A3)."""
        usage = getattr(response, "usage", None)
        reported = getattr(usage, "cost", None) if usage is not None else None
        if reported is not None:
            return {"cost": float(reported), "cost_source": "provider_reported", "cost_missing": False}
        try:
            c = litellm.cost_calculator.completion_cost(response, model=self.config.model_name)
            if c > 0:
                return {"cost": float(c), "cost_source": "litellm_price_map", "cost_missing": False}
        except Exception:
            pass
        return {"cost": 0.0, "cost_source": None, "cost_missing": True}

    def query(self, messages, **kwargs) -> dict:
        attempts, t0 = 0, time.time()
        for attempt in retry(logger=logger, abort_exceptions=self.abort_exceptions):
            with attempt:
                attempts += 1
                response = self._query(self._prepare_messages_for_api(messages), **kwargs)
        latency = time.time() - t0
        cost_output = self._calculate_cost(response)
        GLOBAL_MODEL_STATS.add(cost_output["cost"])
        meta = {
            **cost_output,
            "usage": extract_usage(response),
            "latency_s": latency,
            "attempts": attempts,
            "response_model": getattr(response, "model", None),
            "response_id": getattr(response, "id", None),
        }
        try:
            actions = self._parse_actions(response)
        except FormatError as e:
            # mini-swe-agent drops the failed assistant turn, so the model sees only a bare error and repeats itself
            # (at temperature 0, identical context gives identical output). Show it its own call with a tool result.
            err = e.messages[0]["content"]
            assistant = response.choices[0].message.model_dump()
            assistant["extra"] = {"response": response.model_dump(mode="json"), **meta, "format_error": True,
                                  "timestamp": time.time()}
            calls = assistant.get("tool_calls") or []
            follow = [{"role": "tool", "tool_call_id": c["id"], "content": err, "extra": {"interrupt_type": "FormatError"}}
                      for c in calls] or [{"role": "user", "content": err, "extra": {"interrupt_type": "FormatError"}}]
            e.messages = (assistant, *follow)
            raise
        message = response.choices[0].message.model_dump()
        message["extra"] = {"actions": actions, "response": response.model_dump(), **meta, "timestamp": time.time()}
        return message

    def _parse_actions(self, response) -> list[dict]:
        return parse_actions(
            response.choices[0].message.tool_calls or [],
            self.tool_names,
            self.config.format_error_template,
            response.choices[0].finish_reason,
        )
