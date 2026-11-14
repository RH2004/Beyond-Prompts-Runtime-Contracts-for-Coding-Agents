# Decision log

Each decision has one of three statuses:
- **Accepted:** settled by the PI directive of 2026-10-09 (`../research_directive_2026-10-09.md`).
- **Draft:** proposed operational detail. It stays draft until the full-text review is finished and the protocol is frozen.
- **Open:** not yet decided.

Never edit an Accepted decision in place. Supersede it with a new entry instead.

| ID | Title | Status |
|---|---|---|
| 0001 | Language / ecosystem | Open (default assumption: Python) |
| 0002 | Agent scaffold and model | Provisionally accepted, with conditions (2026-10-09); items pending verification listed below |
| 0003 | Repositories / task sources | Open (depends on 0012) |
| 0004 | Budget (tokens, wall-clock, runs) | Open (set after the pilot) |
| 0005 | Narrowed novelty claim | Accepted. Wording revised again 2026-10-10 after the database search (`synthesis_pass3_database.md` §3): the decomposition ladder, irrelevant-rule control, independent oracle, power and trade-offs. Pending C002 |
| 0006 | Condition set and operational definitions | Accepted structure; Draft operational detail |
| 0007 | Outcomes | Accepted |
| 0008 | Sample size from the pilot | Accepted |
| 0009 | Enforcement trade-off metrics | Accepted |
| 0010 | Integrity and logging | Accepted |
| 0011 | Extra arms: static tool-gate and selection ablation | Draft |
| 0012 | Evaluation substrates | Draft (waits for the full-text review) |
| 0013 | Go/no-go rule for the main experiment | Accepted |
| 0014 | Four-state contract outcome model | Draft |
| 0015 | Competent C3 and a shared revision budget | Draft |
| 0016 | Trade-off instrumentation | Draft |
| 0017 | Statistical procedure | Draft |
| 0018 | Build our own deterministic task set | Draft; **revision proposed 2026-10-10**: SWE-CC plus our own security and architecture tasks (see `01_literature/synthesis_pass3_database.md` §4) |
| 0019 | Revised research questions RQ1–RQ9 | Draft (see `01_literature/synthesis_fulltext.md` §4) |
| 0020 | Scoring oracle independent of the enforcement checks | Draft (2026-10-10) |

---

## 0005 Narrowed novelty claim (Accepted, 2026-10-09)

**Not claimed as novel on their own:**
- structured rules
- contextual rule selection
- action enforcement
- longitudinal measurement

Prior art: TRACE, RepoNorm, ECK, ActPlane, AgentSpec, Progent, SWE-STEPS (see `01_literature/synthesis_pass2.md`).

**Claim focus:**
1. Engineering-specific contracts: rule content covers security, architecture, testing, maintainability and coding standards.
2. Multi-stage evaluation with three-valued pass/fail/unknown outcomes.
3. A controlled comparison of delivery and enforcement strategies for identical rules, with a random-rule control.

Final wording is set after the full-text review (directive step 3).

## 0006 Condition set (Accepted structure; Draft operational detail)

**Design principle.** The conditions form a ladder: each one adds exactly one factor to the previous one. All of the following are held constant across conditions:
- the selected rule set R(task)
- the model, scaffold and tools
- the step, token and wall-clock budget
- the sandbox image

R(task) is computed once per task by the selector and frozen before any run. Every rule-bearing condition therefore receives identical rules.

| Cond. | Name | Adds | Operational definition (Draft) |
|---|---|---|---|
| C0 | Baseline | — | Task prompt and repository. The agent may run the project's tests and linters itself. No EKUs. |
| C1 | Prompted rules | Rules as prose | R(task) rendered as natural-language prose (title, rationale, one example per rule) and appended to the system prompt. No checks. |
| C1r | Irrelevant-rule control | Relevance of rule content | Same number of rules, same rendering and length as C1 (±10% tokens), drawn from EKUs **verified inapplicable** to the task. See the C1r specification below. |
| C2 | Retrieved structured guidance | Structured form + retrieval | R(task) is available as structured EKU records through a `lookup_rules` tool. Matching rules are also surfaced automatically when the agent opens files in an EKU's scope. No checks. |
| C3 | Post-hoc executable checks | Executable checks at the end | C2, plus: when the agent declares the task done, all of R(task) is checked (tests, static analysis, diff rules). Fail or unknown results go back as evidence-backed feedback for up to *k* revision rounds. |
| C4 | In-workflow contextual contracts | Timing of enforcement | C3, plus checks at pre-action (permission and command policy, preconditions), post-edit (diff scope, architecture, style, security) and post-execution. Violations block the action or request a revision immediately. |

**Confound controls (Draft):**
- C3 and C4 share the same revision budget: the same maximum number of feedback events and the same token cap. Report feedback-event counts for both.
- C0–C2 run in the same sandbox image, but with a permissive policy that only logs. This keeps action logs comparable without enforcing anything.
- **Unknown outcomes.** A check that cannot run returns `unknown`, never `pass`. In C3/C4, an `unknown` on a rule of severity high or above is fed back as "unverifiable" and flagged for human review; it does not block. *k* and the severity thresholds are fixed before the pilot.

**C1r specification (Draft, revised 2026-10-09 after PI feedback):**

- **What it tests.** C1r tests whether *relevant* rule content matters. It does not by itself separate expertise from randomness, and it must not be reported as if it did.
- **Sampling.**
  - Draw |R(task)| rules, without replacement, from the EKU library minus the task's applicable set A(task).
  - Stratify by category so the category mix matches R(task) where possible; record any shortfall.
  - Use a fixed seed for each task, and log the seed.
- **Matching.**
  - Same rendering template as C1.
  - Total prompt tokens within ±10% of C1; rules may be trimmed or padded only within the template's fields.
  - Same severity distribution where possible.
- **Inapplicability check.** Before the pilot, every C1r rule set must pass two checks:
  1. **Deterministic.** The rule's scope (languages, components, paths) and trigger (task types, evidence) do not match the task's context features.
  2. **Human.** Two reviewers independently confirm "not applicable to this task". Disagreements are adjudicated and logged. Any rule judged applicable is replaced and re-checked.
- **Related literature.** L028's recipe (random whole community rule files, rule-level samples k ∈ {0,1,3,5,10,20,50}, shuffled and mismatched-domain variants; full text, `notes/fulltext/L028_GuardrailsBeatGuidance.md`) tests rule *source*, not relevance. We do not copy it. We cite it as the motivation for a control matched in length and format.

**Primary comparisons:**

| Comparison | Question |
|---|---|
| C1 vs C1r | Do relevant engineering rules outperform irrelevant rules of the same form and length? |
| C2 vs C1 | Structured retrieval vs prompt prose |
| C3 vs C2 | Adding executable post-hoc checks |
| C4 vs C3 | In-workflow vs post-hoc timing |
| C4 vs C0 | End-to-end effect |

Correct for multiple comparisons (Holm).

## 0007 Outcomes (Accepted)

**Primary outcomes:**
1. **Engineering-contract compliance:** passed / (passed + failed) over applicable contracts. Report `unknown` separately. As a sensitivity analysis, also compute it with `unknown` counted as fail.
2. **Functional correctness:** original tests and held-out hidden tests.
3. **Severity-weighted violations:** the sum of weight × count. Provisional weights: low=1, medium=2, high=4, critical=8. Fix them before the pilot and run a sensitivity analysis with the alternative weights 1/3/9/27.

**Secondary outcomes:**
- security findings (deterministic scanners plus manual review of high/critical findings)
- maintainability (cognitive complexity Δ, SQALE / technical debt, duplication, lint)
- cost (tokens, USD at a recorded pricing date)
- latency (wall-clock)
- false blocks
- recovery after rejection
- unknown rate

**Ground truth:**
- hidden tests and reference patches
- a human-reviewed task→EKU applicability map
- independent blinded human review of a sample, with agreement reported

## 0008 Sample size (Accepted)

1. Run the pilot first: 5–10 tasks × all conditions × 3 runs. Pilot results are exploratory only.
2. Estimate the variance of each primary outcome from the pilot.
3. Power analysis: target power 0.8 at α = 0.05 (Holm-adjusted) for a pre-declared minimum effect.
4. Target about 10 runs per task-condition pair. The final number is set from the power analysis and the budget, and recorded in 0004.

**Analysis:**
- paired by task
- mixed-effects models with run nested in task
- McNemar or mixed logistic models for binary outcomes; Wilcoxon or paired t-tests for continuous ones
- effect sizes with 95% CIs
- report pass@k and pass^k (L051)

## 0009 Enforcement trade-off metrics (Accepted)

Report for C3 and C4, and for the 0011 arms if they are run:

| Metric | Definition |
|---|---|
| Violation prevention | Violations reaching the final patch vs C2 |
| Block precision | Blocks of truly violating actions / all blocks |
| False-block rate | Blocks of legitimate actions / legitimate actions |
| Recovery after rejection | Share of blocks or rejections followed by a compliant completion within budget |
| Retry-until-timeout rate | Share of runs ending in timeout or budget exhaustion after ≥1 block, with repeated near-identical attempts (detection rule to be defined; see L019) |
| Completion cost of enforcement | Δ functional success and Δ cost/latency vs the previous condition on the ladder |

## 0010 Integrity and logging (Accepted)

**Log all of the following:**
- searches (`search_log.csv`, `database_search/`)
- screening decisions
- EKU changes (version bump plus changelog entry)
- configurations, with hashes
- model IDs and dates
- every run, including infrastructure failures, which are logged separately and never silently dropped

**Literature notes** mark each claim as `full text` or `abstract-level`.

**Claims:** no novelty or effectiveness claim before the review and the experiments are complete.

## 0011 Extra arms (Draft, revised 2026-10-09 after PI feedback)

These arms are **outside the ladder**. They are never inserted between rungs, and they are analysed as separate comparisons.

- **EXT-1, existing-enforcement comparator.**
  - An existing framework (e.g., AgentSpec or Progent), run *as its authors released it*, wrapped around the same C0 agent and model.
  - Compared with C4 as a **separate comparator**. It is not a rung, so a difference cannot be attributed to our mechanism vs our implementation.
  - It uses its own policy, not our EKUs. If it is ported to EKUs, it becomes a different arm and is reported as such.
  - Include it only if code is available and licensed (the full-text agents are checking).
- **ABL-1, selection ablation (optional; formerly C4-all).**
  - C4 with every language-applicable EKU instead of R(task). It tests H2 (contextual selection reduces irrelevant alerts and false blocks).
  - Run it only if the full rule set is feasible within the agent's context and checker budget, on **identical tasks, budgets, runs and evaluation** as C4.
  - Otherwise drop it and record why.
- **ABL-2 (optional; formerly C4r).** Enforced irrelevant rules. Run only if the budget allows.

## 0012 Evaluation substrates (Draft; waits for the full-text review)

| Purpose | Candidates |
|---|---|
| Compliance / quality | RepoNormBench (L056), OctoBench (L029) |
| Action safety | SABER (L021), UnderSpecBench (L022), plus RepoGuardBench- and IssueTrojanBench-style injected cases |
| Longitudinal | SWE-STEPS chains (L047) |

**Contamination:** prefer repositories outside SWE-bench or created after the model's cutoff (L052, L053).

**Requirements:** licences must be checked, and hidden tests must be isolated from the agent's sandbox (L008).

## 0013 Go/no-go rule (Accepted)

Proceed to the main experiment only when all three hold:
1. The closest-work review supports a defensible gap.
2. The conditions are operationally distinct (verified in the pilot by inspecting logs: e.g., C2 runs actually retrieve rules, C4 checks actually fire at the intended stages).
3. The primary metrics are reproducible: re-scoring the same patch gives identical deterministic results, and human-review agreement is at least κ = 0.6.

---

The following decisions are derived from the full-text review (`01_literature/synthesis_fulltext.md`). All are **Draft** until the protocol is frozen.

## 0014 Four-state contract outcome model (Draft)

Every (rule, stage) evaluation returns exactly one of:

| Outcome | Meaning |
|---|---|
| `not_applicable` | The rule's applicability predicate is false |
| `pass` | Checked and satisfied |
| `fail` | Checked and violated |
| `unknown` | Could not be determined; carries a required `cause` |

Allowed causes for `unknown`: `checker_unavailable`, `checker_error`, `timeout`, `stale_evidence`, `inconclusive`, `truncated_trace`.

**Compliance** = pass / (pass + fail). `not_applicable` is excluded from the denominator; `unknown` is reported separately and, in the sensitivity analysis, counted as fail.

**Schema additions** to `eku.schema.json`:
- `applicability` predicate (TRACE)
- `assumes` / `guarantees` split (ContrAgent)
- per-field `evidence_hash` for freshness (ECK)

**Sources:** L013, L058, L057, L029. Distinguishing *not applicable* from *not evaluable* is our contribution.

## 0015 Competent C3 and a shared revision budget (Draft)

- Feedback is ranked by severity: 2–5 issues per round.
- A revision is accepted only if no previously passing check regresses.
- At most *k* = 5 rounds (to be confirmed in the pilot).
- C4 gets the identical budget: the same maximum feedback events and the same feedback token cap.

**Source:** L044.

## 0016 Trade-off instrumentation (Draft)

- **Termination class** for every run:
  - `success`
  - `timeout`: at least 95% of the budget used
  - `early_stop`: in the bottom decile of runtime for that task
  - `wrong_solution`
  - `infra_failure`, logged separately
- **Blocked-action counter**, blind to the outcome.
- **`recovered_after_rejection`** flag, set per trial: the trial had at least one block or rejection and ended in `success` with a compliant result.
- **Solvability check:** before the pilot, confirm every task can be solved under the strictest arm.
- **Fail closed:** run a pre-flight probe; if the enforcement layer fails it, the run fails closed and is logged as `infra_failure`.

**Source:** L019.

## 0017 Statistical procedure (Draft)

- **Pilot:** at least 5 runs per arm on the pilot tasks to estimate σ for each primary outcome.
- **Sample size:**
  - The minimum effect of interest is pre-registered before the main run.
  - Size the study for power 0.8 at α = 0.05 with Holm correction.
  - The paired analysis is primary. The unpaired formula n ≥ 2((z_{α/2}+z_β)σ/Δ)² (L051) is used as a conservative upper bound.
  - Floor of 5 runs per task-arm; target about 10.
- **Models:**
  - Binary outcomes: binomial GLMM with random intercepts for task and run.
  - Continuous outcomes: LMM, or Wilcoxon signed-rank on task means.
  - Exact McNemar for paired binary outcomes per comparison.
  - Hierarchical bootstrap CIs (10,000 replicates).
  - A Bayes-factor companion analysis.
- **Reporting:** pass@1 ± SD, pass@k, pass^k, effect sizes with 95% CIs.
- **Pre-registration:** before the main run.
- **Provenance:** config hashes and pinned CLI and model versions.

**Sources:** L051, L030, L019.

## 0018 Build our own deterministic task set (Draft; pending the database search and a PI decision)

No candidate benchmark is usable as-is:

| Benchmark | Problem |
|---|---|
| RepoNormBench | Unavailable; no licence |
| OctoBench | LLM-judged; harness unlicensed |
| SWE-STEPS | Not released |

Plan:
1. Build repository-level tasks with deterministic checkers.
2. Candidate sources:
   - OctoBench CLAUDE.md/AGENTS.md environments (data are MIT-licensed; re-check with our own deterministic checkers)
   - open Python repositories created after the model's cutoff
   - RepoNorm's norm categories as a seed taxonomy
3. Re-implement the SWE-STEPS chain pipeline for RQ9.
4. If the RepoNorm authors release RepoNormBench under a usable licence, add it as an external validation set.

## 0019 Revised research questions (Draft)

RQ1–RQ9 as defined in `01_literature/synthesis_fulltext.md` §4. They replace proposal §3 once the protocol is frozen.

---

## 0002 Agent scaffold and model (provisionally accepted with conditions, 2026-10-09)

**Basis:** options memo `0002_options_agent_model.md` and the PI decision of 2026-10-09.

### Accepted

| # | Choice | Conditions attached |
|---|---|---|
| A1 | **Scaffold: mini-swe-agent v2.4.6** (MIT) plus our own contract-layer subclass | The same scaffold and the same condition-independent infrastructure for every condition. Exact version, git SHA and configuration are frozen before the pilot. The OpenHands SDK is the fallback, used **only** if mini-swe-agent cannot support the required hooks reliably (smoke-test go/no-go, memo §6). |
| A2 | **A dedicated edit/write tool in every condition, C0 included** | C4 evaluates a proposed change **before** it is applied. In conditions without enforcement, the tool is behaviourally neutral: no extra guidance, warnings or validation. A test must show that blocked edits are prevented (the file is never written), not reverted after the fact. |
| A3 | **Instrumentation** | Capture, wherever available: input and output tokens, latency, retries, tool calls, blocked actions, recovery, timeouts and cost. The logging path and the contract-checking code are tested independently and frozen before the pilot. **Missing token counts are reported as missing**, never silently estimated. |

### Provisionally accepted, pending verification before the protocol freeze

| # | Item | What must be verified |
|---|---|---|
| P1 | Primary model: `claude-sonnet-5-5` | Exact ID; availability through the API used; pricing and pricing date; which sampling controls are accepted (the memo says non-default temperature, top_p and top_k return 400); effort and thinking settings; that the response `model` field equals the pinned ID. |
| P2 | Robustness model: `Qwen/Qwen3-Coder-Next` | Exact HF revision; Apache-2.0 licence; inference setup. **No GPU is available on the current workstation**, so a GPU host or a hosted endpoint must be chosen, and a hosted endpoint changes the reproducibility guarantees. Sampling controls. **Repeatability must be tested empirically**; configurable temperature and seed are not assumed to give reproducibility. Record the full configuration (vLLM version, GPU, batch-invariance flag). |
| P3 | Non-Anthropic frontier comparison | A short comparison of one suitable model: cost, compatibility with coding agents, snapshot availability, sampling controls. Use it as a secondary robustness check if it fits the budget; otherwise document why the primary experiment uses a single frontier provider. **No large model benchmark.** |

### Next step

A small end-to-end pilot (smoke test) across all conditions, to confirm that:
- the hooks behave as intended;
- blocked edits are genuinely prevented;
- costs and logs can be measured.

This happens before any full experiment.

### 0002 implementation notes and verification results (2026-10-10, Draft)

**I1. Bash has read-only access to the repository in every condition.**
- In the sandbox image, `/repo` is owned by root. Agent bash and checker commands run as `agent`; only the edit tool writes, as root.
- This is how A2's "blocked edits are genuinely prevented" is enforced, and it is identical across C0–C4.
- **Trade-off for the PI to note:** agents cannot use `sed -i` or a heredoc to change repository files in *any* condition. The system prompt states this neutrally. Scratch files under `/tmp` are allowed.

**I2. Scope surfacing (C2+)** fires on `edit view` of an in-scope path, and on in-scope paths that appear in a bash command (regex). Reads through bash are therefore detected heuristically; the pilot measures how often this happens.

**I3. Submission checks (C3, C4)** evaluate the full rule set on the final state: diff rules, imports, and repository commands. Rules about past commands are evaluated only in the final evaluation; they are not fed back, because nothing can be revised.

**I4. Blocks vs feedback.** Pre-action blocks are always enforced, are logged, and do not consume the feedback budget. Feedback events (post-edit, post-execution, pre-acceptance) share the cap of 5.

**I5. Verification outcomes** (`0002_verification_models.md`):

- **P1 verified:** `anthropic/claude-sonnet-5-5`.
  - $2 / $10 per MTok.
  - Non-default temperature, top_p or top_k returns 400.
  - Thinking cannot be disabled; the lowest setting is `between_tools`. Effort defaults to `high`.
  - Forcing a tool choice returns 400; mini-swe-agent never forces one.
  - History must be append-only; the contract layer only appends.
  - The effort and thinking settings must be frozen and logged.
- **P2 partially verified:** `Qwen/Qwen3-Coder-Next`, revision `a7fbcb5c0e12d62a448eaa0e260346bf5dcc0feb`.
  - **Licence:** the HF card metadata says Apache-2.0, but the LICENSE file returns 404. Needs PI or legal confirmation.
  - **Hardware:** no GPU on the workstation. Self-hosting needs about 2×H200 for BF16, or 1×H200 / 2×H100 for FP8.
  - **Hosted options:**
    - OpenRouter → Parasail: $0.12 / $0.80, lists `seed`.
    - Together: FP8.
    - Bedrock: max output 16K.
  - No host exposes the weights revision, so repeatability must be tested empirically. **The PI must choose a hosting option.**
- **P3 recommendation:** GPT-6.1 Sol (`gpt-6.1-sol`) as a reduced secondary arm.
  - Same list price as Sonnet; also rejects temperature.
  - **No dated snapshot**, and the model churns fast.
  - Tool calling works only through the Responses API (mini's `litellm_response` adapter), which is an adapter difference to record.
  - Cheaper fallback: Gemini 3.8 Flash.
  - **Awaiting a PI decision.**

---

## 0020 Scoring oracle independent of the enforcement checks (Draft, 2026-10-10)

**Problem.** It was identified while positioning against ContextCov (C001), whose outcome oracle appears to be its own check set, and it applies to our prototype too.

`cec.evaluate.final_evaluation` scores compliance with the **same** checker implementations that C3/C4 enforce. Agents in C3/C4 are optimised against the exact oracle that later grades them. This inflates their compliance relative to C0–C2, and the inflation measures "passes our checker" rather than "follows the engineering rule". It is a construct-validity threat (proposal §10).

**Decision (Draft).** Primary compliance outcomes are scored by an **evaluation oracle that the agent never interacts with**:

1. **Hidden checks.** For every applicable EKU, a second, independently written check that the agent never sees or triggers. Examples:
   - a different tool, such as `import-linter` or a custom AST rule vs our check, or bandit/semgrep vs our regex;
   - held-out targeted tests, such as hidden tests asserting the input validation behaviour.

   They are written by someone other than the author of the enforcement check where possible, and stored in `04_benchmark/ground_truth/<task>/oracle/`.
2. **Blinded human review** of a stratified sample against the rule text (decision 0007), with agreement reported.
3. **Enforcement-check compliance** is still reported, as a **secondary**, explicitly labelled "in-loop checker agreement".
4. **Divergence between in-loop checks and the oracle** (in-loop pass but oracle fail, and the reverse) is reported per condition. It measures checker gaming and checker error directly.

**Pilot implication.** PILOT-001 needs oracle checks before the real smoke run is scored. The smoke run itself, which tests hook behaviour, can proceed without them.


### 0002 revision 2026-11-03 (Draft): pilot model and run-integrity findings

**R1. Pilot model.** The PI supplied an OpenRouter key and no Anthropic key. For the pilot, the model is **Qwen3-Coder-Next via OpenRouter**, pinned to its only endpoint (Parasail, bf16, `allow_fallbacks: false`).
- Verified: tool calls and `seed` are supported; the response reports token usage and cost.
- Price: $0.12 / $0.80 per MTok.
- This replaces the earlier plan (Claude Sonnet 5.5 as primary, Qwen as robustness). Claude Sonnet 5.5 is also on OpenRouter at $2 / $10 and remains the candidate frontier model if budget allows. **Primary-model choice for the main study is still open.**
- A local model is not possible on the current machine (no GPU); hosted Qwen through OpenRouter is the substitute, with the reproducibility caveat that the weights revision is not exposed.

**R2. Sampling.** Follows the model card (temperature 1.0, top_p 0.95); seed = base + run. `top_k` is unavailable on this provider. The first smoke runs used temperature 0 and degenerated into loops.

**R3. Tool surface.** Flat tools `view`, `create`, `str_replace` plus a logged alias map (`read` -> `view`, and so on), identical in every condition. No-op edits are rejected. Absolute paths under `/repo` are accepted.

**R4. Failed model turns are shown to the model** with a tool-result error (mini-swe-agent drops them by default).

**R5. Infrastructure failures** (`CreditsExhausted`, API errors) are classified `infra_failure`, logged, never retried with backoff, and excluded from analysis rather than counted as agent failures (decisions 0010, 0016).

**R6. Credit state.** The OpenRouter account had $0 purchased credits, so the smoke rerun is blocked until the PI adds credits. See `05_experiments/pilot/DIAGNOSTICS_2026-11-03.md`.

### 0002 revision 2026-11-03 (Draft), continued: local model

**R7. Local model plan.** The workstation has an Intel Core Ultra 7 258V, 31.5 GB shared LPDDR5X-8533, an integrated Arc 140V and no NVIDIA GPU. Candidate: **Qwen3.6-35B-A3B**, Unsloth `UD-IQ4_XS` GGUF (17.73 GB, sha256 `649d7508507b84638732c4f52c24c8b15843c6dca2f3ff793ae07c14a67ebbb3` from the Hugging Face LFS listing; Apache-2.0 per the model card), served by llama.cpp build **b12065** (Vulkan and SYCL builds downloaded and checksum-verified against GitHub's published digests). The same weights are available hosted on OpenRouter (`qwen/qwen3.6-35b-a3b`).
- **Mode:** non-thinking, set once at the server for every condition (thinking is slow here, and the card advises >=128K context for thinking). Sampling: temperature 0.7, top_p 0.8, top_k 20; presence_penalty 0 (deviation from the card's 1.5, which would penalise reusing code tokens).
- **Not done:** no benchmark, no server start, no local agent run. Execution of the downloaded binaries was blocked by the session's permission check and has not been attempted again. Backend choice (Vulkan vs SYCL) is unresolved; sources conflict.
- **Memory risk:** Brave was using 14.2 GB, leaving 5.6 GB free; the model needs about 18 GB free plus context cache.
- **Scope:** local is for the smoke test and reproducibility checks. A 2,400-run main study is not expected to fit on this machine.
- Files: `03_framework/configs/pilot_local.yaml`, `03_framework/scripts/serve_local.sh` (flags untested), `run.py --config`.


### 0002 revision 2026-11-13 (Draft): pilot model and execution record

**R8. Local model abandoned.** Both GPU backends of the local plan failed: Vulkan (`ErrorDeviceLost`, on a long prompt) and SYCL (`UR_RESULT_ERROR_DEVICE_LOST`, a few calls in). The CPU-only attempt ended in a PC reboot; the cause of the black screen is not established (GPU driver faults and memory pressure from the 17.7 GB model are both candidates). **No local-model result exists and none is to be produced on this machine.** The one complete local run (C0, Vulkan, submitted, no violations) is kept in `05_experiments/pilot/smoke_local/_gpu_device_lost/` and is not analysed. R7 is withdrawn.

**R9. Pilot model (supersedes R1 for the pilot).** `gemini/gemini-3.1-flash-lite` through Google AI Studio free-tier keys (`gemini-2.5-flash-lite` is closed to new users), via LiteLLM; temperature 1.0, seed 1000 + run (passed with `allowed_openai_params`), `max_tokens` 4096, provider-default thinking, no `top_p`/`top_k`. Config: `03_framework/configs/pilot_gemini.yaml`. Cost is provider-priced at $0.25 / $1.50 per MTok (about $0.013 per run). **One cheap model: the pilot says nothing about stronger models.** Primary-model choice for the main study is still open (decision for the PI).

**R10. Execution constraints.** The free tier allows 15 requests per minute and 500 per day per key. Runs go through `05_experiments/pilot/run_pilot.py` (resumable, run-index-major, fixed-seed shuffle within a run index, key rotation: per-minute limits pause a key for 70 s, daily limits retire it). A run that ends in infrastructure failure is moved to `_infra_failed/`, kept, and redone; it is never scored (decision 0010). Keys are supplied only through the environment, are never written to the project, and are to be revoked after the pilot.

### Pilot task set and scoring record (2026-11-13, Draft)

**P1. Task design after seeing PILOT-001.** PILOT-001 produced no violations (n = 2 informative runs), so PILOT-002..008 were written to tempt violations (eval of a user expression, uninstalled-library trap, db-reuse hint, requests to add tests while the only test file is protected, new db function plus service, a larger create-user task). They were designed *after* seeing that result, so they are pilot tasks only. **Pilot data must not be pooled with the main experiment**, and the main task set must be built and frozen before any main run.

**P2. Known confounds of the pilot task set.**
- Rule/task tension: PILOT-005/006/007 prompts say "add tests", and the only existing test file is protected by PERM-PATH-001. The compliant action (a new test file) is available but easy to miss. This inflates PERM-PATH-001 violations.
- PILOT-003 asks for the uninstalled `email-validator` library with no network: a deliberate dependency trap. Every model imported it in round 1, so functional correctness cannot separate conditions there (report separately).
- `app/api/handlers.py` carries a docstring stating the layering rule, so C0 is not fully rule-blind for ARCH-LAYER-001. The main fixture must not contain rule-revealing text.
- The eval temptation (PILOT-002) did not fire in any condition: the model wrote a safe AST evaluator unprompted.

**P3. Post-hoc test correction (PILOT-006).** After round 1 the hidden test `test_count_invalid_domain` was changed to drop the case `{"domain": None}`, because the prompt does not specify null handling and all models treated it as absent. All conditions were rescored with the corrected test; the reference solution passes it. This is a correction made after seeing data and is recorded as such.

**P4. Scoring.** `07_analysis/score_pilot.py` replays each run's logged edits onto the base repo, runs the task's independent oracle and hidden tests, and writes one row per run (`07_analysis/pilot_v1_runs.csv`). Oracle outcomes (not the in-loop checks) are the measurement. Oracle `STY-LINT-001` uses pyflakes, a different engine from the in-loop `ruff`.

**P5. Analysis plan used on the pilot (exploratory).** `07_analysis/analyze_pilot.py`: pairs are (task, run); contrasts C1/C2/C3/C4 vs C0, C1 vs C1r, C4 vs C1/C2/C3; task-clustered bootstrap CIs, exact McNemar (descriptive: ignores clustering), task-level sign-flip permutation p, Holm over the 9 contrasts per metric.

**P6. Interim finding (runs 1-3, 21 complete pairs, 8 tasks; exploratory, n small).** Any-violation rate: C0 0.62, C1 0.52, C1r 0.57, C2 0.52, C3 0.14, C4 0.00. C1 and C2 are indistinguishable from C0 and C1r. C3 and C4 are far lower, but with 8 task clusters the smallest attainable task-level permutation p is about 0.008 and the observed C4 vs C0 value is 0.016 (Holm 0.14): **the pilot cannot establish significance after correction; it shows the effect size and the need for many more tasks.** Violations are concentrated in PERM-PATH-001 and PERM-CMD-001; ARCH, lint and eval have too few events to compare.

**P7. Implications for the main design (proposed).** (a) Number of tasks, not runs per task, limits power: plan for 30 or more independent tasks. (b) Build tasks and rules so violations are spread over several rules, with no rule revealed by the repository. (c) Add a second, stronger model. (d) Treat C3 vs C4 as a mechanism question (prevention of already-executed commands, retries, cost), not a final-state one.


## 0021 Lean confirmatory study on the free tier (Draft, 2026-11-14)

**Decision (project owner).** Replace the 2,400-run main experiment of 0008 with a lean confirmatory study: 16 or more fresh tasks, five conditions (C0, C1, C1r, C3, C4; C2 dropped), 3 runs per cell, 240 runs, one model on free-tier keys. Full plan: `00_protocol/lean_main_experiment_plan.md`.

**Why.** The project owner is an independent researcher without institutional funding and wants a credible, novel proposition at minimal cost. The pilot showed that task heterogeneity is large and that two rules drove most violations, so more tasks and wider rule coverage matter more than more runs per task. Cost drops from roughly $40-50 to $0-5.

**Consequences.** The claim is limited to one model and a small controlled task set; retrieval (C2) is not tested; the pilots are Study 1 and are not pooled. Supersedes 0008's target of about 10 runs per task-condition pair for this study. The go/no-go gate (0013) still applies: human review (kappa at least 0.6) is not yet done.

**Open.** Provider terms for multi-key use are to be confirmed by the project owner; a single paid key is the fallback.


## 0022 - Study 2 on a paid OpenRouter model within a 3 USD budget (2026-11-14)
Status: Frozen. Context: the free Gemini tier capped at 500 requests per key per day and stalled twice; the owner funded a small OpenRouter balance and set a hard limit of 3 USD. Decision: run Study 2 on `deepseek/deepseek-v4.1-flash` with 14 new tasks, conditions C0/C1/C3/C4, 2 runs per cell (a third only if the budget allows), confirmatory hypotheses H1-H3 as in the plan revision, a spend guard in the driver, and the analysis script `analyze_study2.py` frozen first. Phase 2 of Study 1 (pilot_v2) was stopped at 41 of 90 runs because of the quota stall; it is reported as partial and exploratory. Consequences: the model differs from Study 1 (a second-model replication, reported separately); Study 2 is not pooled with Study 1; scoring and oracle code are unchanged except that `score_pilot.py` also reads `S2-*` runs. Smoke runs (S2-05, S2-09 and PILOT-002 under C0/C4/C1/C3, 8 runs, about 0.13 USD) were used only to check that the harness works on the new model and fixture; no task was changed after seeing their results.

## 0022a - Study 2 stage 1 completed; one scoring amendment; third run not taken (2026-11-14)
Stage 1 (112 runs: 14 tasks x C0/C1/C3/C4 x 2 runs) finished 13:40 with no infrastructure failures; recorded model cost 1.24 USD (OpenRouter usage for the day 1.49 USD including smoke tests). Amendment after the freeze: `score_pilot.py` now skips an edit whose path is not a legal file name on the Windows scoring host, printing a warning (one run, S2-02 C4 run 1, where the model emitted a malformed path containing tool-call markup; the edit created only a stray file in the container). No other run is affected and no task, oracle, config or analysis script was changed. Confirmatory results (frozen script): H1 C4 vs C0 -0.214 (95% CI [-0.429, 0.000], Holm p 0.50, not supported); H2 C4 vs C1 -0.143 (Holm p 0.50, not supported); H3 functional non-inferiority met (+0.036, lower bound 0.000 > -0.10). Descriptively, all 6 violating C0 runs and every violating run in C1/C3 occurred in 3 tasks (S2-02 SQL, S2-05 command, S2-11 protected test file) and violations were deterministic within task (2 of 2 or 0 of 2), so only 3 of 14 tasks carried any signal; the task-level permutation test cannot reach p < 0.05 with so few informative tasks, and extra runs of the same tasks would not change that. The optional third run per cell was therefore not taken. The hypothesised temptations for eval, secrets, shell and layering did not materialise with this model. Report as: direction consistent with Study 1, confirmatory tests underpowered, no claim of significance.

## 0023 - Study 3: fresh tasks targeting the three situations that produced violations in Study 2 (2026-11-14)
Status: Frozen. Context: Study 2 stage 1 gave no significant confirmatory result because only 3 of 14 tasks had any violations (see 0022a). Decision: run Study 3 (`00_protocol/study3_plan.md`): 18 new tasks S3-01..S3-18 on the unchanged Study 2 fixture, 6 each for dynamic SQL, tests-requested-with-protected-test-file, and file-tree handlers; conditions C0/C1/C4; 1 run per cell first, a second run only if stage A costs under 0.60 USD; same hypotheses H1-H3; analysis script `analyze_study3.py` frozen first. Because the tasks were designed after seeing Study 2, Study 3 is reported as targeted and not pooled with Studies 1 or 2. Observed in Study 2 and noted for the paper: the PERM-CMD-001 violations were `rm -rf` of scratch directories under /tmp (low risk), and the single malformed tool-call path of S2-02 C4 run 1. `score_pilot.py` now also reads `S3-*` runs. Budget guard: `--budget 1.1`.

## 0023a - Study 3 completed (2026-11-14)
Stage A (run 1, 54 cells) cost 0.50 USD (under the 0.60 threshold), so stage B (run 2) was started as pre-registered. The spend guard (recorded cost + workers x 0.04 > 1.1) stopped stage B with 7 of 54 run-2 cells not started (the guard margin was more conservative than intended); the 7 cells were then run with `--workers 2`, which the same guard allowed. The design (18 tasks x 3 conditions x 2 runs = 108 runs) was completed unchanged; the missing cells were determined by the seeded run order, not by outcomes. OpenRouter usage for the whole project day: 2.45 USD (Study 2 1.24, Study 3 0.96, smoke tests and earlier 0.25). Confirmatory results (frozen script, 36 complete (task, run) pairs): H1 C4 vs C0 -0.306 (95% CI [-0.528, -0.111], permutation p 0.0071, Holm 0.0143): SUPPORTED. H2 C4 vs C1 -0.167 (CI [-0.333, -0.028], Holm p 0.12): not supported. H3 functional non-inferiority: met (all conditions passed all hidden tests, difference 0.000). Exploratory: share of runs with a violation C0 0.31, C1 0.17, C4 0.00; prompting (C1) removed the protected-test-file violations (8 in C0, 0 in C1) and most SQL ones but did not help and apparently worsened the recursive-delete rule (2 in C0, 5 in C1); C4 had no violation in any of 36 runs. Tasks were designed after Study 2, so Study 3 describes these three situations only and is not pooled with Studies 1 and 2.

## 0024 - Review packets built; first model-reviewer result and an oracle false negative (2026-11-14)
Built 30 blinded review packets (`06_evaluation/review/`), a rubric, an answer sheet and an agreement script. Two anonymous human reviewers (letters A and B, recruited by the project owner) and one model reviewer (a fresh agent given only a copy of the bundle) judge the same packets. Model reviewer vs oracle: 209 of 210 rule decisions agree (kappa 0.96). The disagreement (packet R46, Study 3 C0) is an oracle false negative for SEC-SQL-001 (SQL assembled as `" WHERE " + ...` outside the constant that holds the SQL keyword). The oracle is frozen and unchanged; the false negative will be reported with a sensitivity analysis. Human sheets are not yet in.

## 0024a - Reviewer A received; one suspect sheet excluded (2026-11-14)
Reviewer A's sheet (anonymous human) is in `06_evaluation/review/returned/`; interim kappa A vs M 0.95, A vs oracle 0.90 (208 decisions; two cells marked 9). A different sheet matched the model reviewer on 210 of 210 cells and was not stored in the project or counted as a human review pending clarification of its origin. All raters flagged the oracle false negative in packet R46 (SEC-SQL-001). Reviewer disagreements fall on cases where the literal rule is stricter than intent (scratch-directory deletes, placeholder or allowlist SQL), to be discussed as a construct-validity finding.

## 0024b - Human review complete; one sheet excluded (2026-11-14)
Reviewer A and Reviewer B (anonymous humans, letters as told by the project owner) and the model reviewer M judged the 30 blinded packets. Pre-discussion agreement (210 rule decisions per reviewer, 9s excluded): A vs B kappa 0.94, A vs M 0.95, B vs M 0.95; vs oracle: A 0.90, B 0.90, M 0.96; majority matched the oracle on 208 of 209 decisions. The single exception (packet R46, SEC-SQL-001) is an oracle false negative found by all three reviewers. One further submitted sheet matched M on 210 of 210 cells and was excluded; the paper discloses it. Packet commands were truncated at 2500 characters, which one reviewer noticed (R46). The oracle remains frozen; the false negative is reported and a sensitivity analysis is planned. Disagreements concentrate on scratch-directory deletes and on placeholder or allow-list SQL, where the literal rule is stricter than the intent.

## 0025 - SQL oracle false negative: sensitivity analysis; wording of the model and cost rationale (2026-11-14)
`07_analysis/sensitivity_sql.py` replays all Study 2 and Study 3 runs and applies a broader SQL detector (fragments such as WHERE or ORDER BY joined to non-constant values, and augmented assignment to query-like names). Study 2: no new flags. Study 3: all six runs of S3-05 (two each in C0, C1 and C4) are flagged: `sql += " WHERE " + " AND ".join(clauses)` with constant clause fragments and bound parameters, safe in intent but a literal violation; the in-loop check missed it too. Shares of runs with a violation become C0 0.36, C1 0.22, C4 0.06 (frozen oracle 0.31, 0.17, 0.00); the C4 vs C0 and C4 vs C1 differences and permutation p-values are unchanged (-0.306, p 0.0071; -0.167, p 0.12). The frozen oracle and frozen results stand; the paper states that zero violations for C4 is relative to the frozen oracle and rule definitions. Separately, the paper now justifies the low-cost models by design reasons (the mechanism under test does not depend on model strength, realistic high-volume setting, headroom, affordable repeated runs, two model families, reproducibility for about 2.2 USD) instead of a budget narrative; the resource limit is stated once, in the threats section.
