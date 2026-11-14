# Framework: contract layer for mini-swe-agent

Implements decisions 0002 (A1–A3), 0006, 0014–0016. One agent class runs every condition. Condition flags (`cec/conditions.py`) switch hooks on or off; nothing else differs.

## Modules (`src/cec/`)

| Module | Role |
|---|---|
| `outcomes.py` | Four-state outcomes (`not_applicable` / `pass` / `fail` / `unknown` + cause); compliance and severity-weighted metrics |
| `eku.py` | Loads and validates EKUs against `02_ekus/schema/eku.schema.json`; prose rendering (C1, C1r); record rendering (C2+); freshness check |
| `checks.py` | Executable checks. A missing checker, a timeout, an unparseable file or a stale rule returns `unknown`, never `pass` |
| `edit_tool.py` | Dedicated edit tool, identical in all conditions. `propose()` never writes; `apply()` writes. Local and Docker file ops |
| `model.py` | LiteLLM model with the condition's tool set. Per call it records token usage (missing values recorded as missing), latency, retry attempts and the response model ID |
| `agent.py` | `ContractAgent(DefaultAgent)`: pre-action blocking, post-edit and post-execution feedback (C4), submission checks with bounded revision (C3+), scope surfacing and `lookup_rules` (C2+), shared feedback budget |
| `evaluate.py` | Final-state and history evaluation, identical for every condition |
| `evidence.py` | Append-only JSONL evidence log; config and code hashes |
| `selector.py` | Deterministic applicability predicate (C1r inapplicability check; seed of the contextual selector) |
| `run.py` | Builds one (task, condition, run) under Docker; writes `evidence.jsonl`, `trajectory.json`, `final_evaluation.json` |
| `stamp.py` | Writes `evidence_hash` into rules only after the validation tests pass |

## Sandbox (`sandbox/Dockerfile`)

`/repo` is owned by root and is read-only for the `agent` user. Agent bash commands and checker commands run as `agent`; the edit tool writes as root. The edit tool is therefore the only write path in every condition, and a C4 block means the file is never written. Network is `none` inside the container; the model is called from the host.

## Tests (no API key or Docker needed)

```bash
.venv/Scripts/python -m pytest -q -p no:cacheprovider tests
```

- `test_core.py` covers the outcome model, the edit tool (propose does not write), pass/fail examples for every pilot rule, unknown causes, freshness, and C1r inapplicability.
- `test_condition_fidelity.py` replays one scripted trajectory that violates one rule per stage under all six conditions. It asserts that:
  - system prompts differ only by the rules block;
  - C1r is within ±10% of C1's length (characters for now; tokens once a tokenizer is pinned);
  - each condition exposes the right tools;
  - retrieval appears only in C2+, and enforcement only in C3 and C4;
  - C4 blocks are genuine prevention (no execution, no write);
  - C3 and C4 share one revision budget;
  - unknown results are flagged but do not block;
  - tool output is byte-identical across C0, C1 and C1r;
  - missing token counts are recorded as missing.

Pinned environment: `requirements.lock` (Python 3.14.6 on the workstation; the sandbox image uses Python 3.12).
