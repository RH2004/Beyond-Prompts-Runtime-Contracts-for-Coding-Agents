# Experiments: layout and status (updated 2026-11-14)

| Folder | What | Model | Status |
|---|---|---|---|
| `pilot/pilot_v1/` | Study 1, exploratory: 8 tasks (PILOT-001..008) x 6 conditions x 5 runs = 240 runs | Gemini 3.1 Flash-Lite (free tier) | Complete, scored (`07_analysis/pilot_v1_runs.csv`, report `pilot_v1_report.md`) |
| `pilot/pilot_v2/` | Study 1 phase 2, exploratory: fixture 2, PILOT2-001..003 | Gemini 3.1 Flash-Lite | **Partial** (41 of 90) and stopped on 2026-11-14 because the free tier daily cap stalled it; not scored; see `pilot/pilot_v2/PARTIAL.md` |
| `smoke_gemini/`, `study2_smoke/`, `study2_smoke2/` | Harness smoke tests | Gemini / DeepSeek | Not analysed (harness checks only) |
| `smoke_local/_gpu_device_lost/`, `local_bench/` | Abandoned local-model attempt | Qwen (llama.cpp) | Quarantined, never analysed; local models are off-limits |
| `study2/main/` | **Study 2, confirmatory**: 14 tasks (S2-01..S2-14) x C0/C1/C3/C4 x runs | `openrouter/deepseek/deepseek-v4.1-flash` | Frozen 2026-11-14 13:10 (`00_protocol/study2_freeze.json`); 112 runs complete, scored (`07_analysis/study2_runs.csv`, `study2_report.md`); H1/H2 not significant, H3 met |
| `study3/main/` | **Study 3, targeted confirmatory**: 18 fresh tasks (S3-01..S3-18) aimed at SQL / protected tests / recursive delete, C0/C1/C4 x 2 runs | same DeepSeek model | Frozen 2026-11-14 14:11 (`00_protocol/study3_freeze.json`); 108 runs complete, scored (`07_analysis/study3_runs.csv`, `study3_report.md`); H1 supported, H2 not, H3 met |

Study 1 and Study 2 are never pooled. Infrastructure failures are moved to `_infra_failed/` inside each run folder and redone.
Run command and resume notes: `pilot/RESUME.md`.
