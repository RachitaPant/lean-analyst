# Lean Analyst: Phase-Wise Project Plan

A GenAI data-analyst agent for business analytics, evaluated on **DABstep** (Adyen + Hugging Face).

Forked from Lean Agents on 2026-10-12. Its Phases 0–2 (setup, foundations, deployed walking skeleton) and its C1/C2 work on BFCL are inherited; see the history in [PHASE_LOG.md](PHASE_LOG.md). This plan starts with the pivot.

**Assumptions:**
- ~10–12 hours/week alongside college. Lean Agents continues in parallel, so expect ~5–6 h/week here.
- Target finish: April 2027.
- An exam buffer is included; move it to match your calendar.

**Principles:**
1. **Reuse, don't rebuild.** The runner, eval harness, guard, server, web trace and provider-error handling carry over. Only the task source, the agent type and the C1/C2 internals change.
2. **Stay live.** The demo is redeployed on DABstep at the end of Phase A, and every improvement ships to it.
3. **C1 first.** The manual alone is ~5.5K tokens against Groq's 8K tokens/minute, so token budget is the gate for everything else.
4. **Honest evaluation.** Use our own labels, never reconstructed answers (see `CLAUDE.md`). Freeze the local set. Make only a few, planned leaderboard submissions.
5. **Never write a number that wasn't measured.**

Progress tracking: tick boxes as you go.

---

## Phase A: Pivot to DABstep (Weeks 1–3)

**A1. Verify before building**
- [x] Download the DABstep context files + `tasks/dev.jsonl` + `tasks/all.jsonl` to `data/dabstep/`; record file hashes and the dataset revision
- [x] Read the leaderboard Space's files (`run.py` baseline, scorer, submission format). Record:
  - whether all 450 answers are required per submission
  - submission limits, and whether an HF login is needed
  - the scorer's license (vendor it only if the license allows; otherwise reimplement from the described rules)
- [x] Read `manual.md` and `payments-readme.md` end to end; write `docs/DOMAIN_NOTES.md` (fee-rule logic, fraud/fines, ACI, capture delay, MCC) in your own words

**A2. Adapter and scorer**
- [ ] `agent/dabstep.py`: task loader (dev/all), context loader (pandas; cache parsed frames), answer scorer (numeric tolerance, normalized + fuzzy strings, lists), submission writer
- [ ] Scorer tests: all 10 dev answers score 1.0 against themselves; known near-misses score as specified

**A3. Agent swap**
- [ ] Baseline agent = stock smolagents `CodeAgent` with the restricted `LocalPythonExecutor`. Authorized imports: `pandas`, `numpy`, `json`, `math`, `datetime`, `re`. Data files read-only, by path; full manual in the prompt (the DABstep-style baseline)
- [ ] Executor hardening tests: no network, no file writes, no imports outside the allow-list, no reads outside `data/dabstep/`; time and memory caps per step
- [ ] `agent/runner.py`: emit `code` and `execution_result` trace events (keep the existing event schema; add fields, don't break the UI)
- [ ] Port `eval/configs.py` and `eval/run.py` to DABstep tasks (resumable, quota-aware; outcome categories gain `code_error`, `format_fail`, `wrong_answer`)

**A4. Demo redeploy**
- [ ] Presets = 4–6 easy and medium dev-style business questions (from `dev.jsonl` + clearly marked custom questions)
- [ ] Web: render code blocks, execution output, final answer vs expected (dev only), and a simple chart when the agent returns a small table
- [ ] Bundle the data with the API service (check the 500 MB limit and cold-start time); a new Vercel project + new Upstash DB (don't share quota counters with Lean Agents)

**A5. Clean up**
- [ ] Remove `agent/bfcl_adapter.py`, `third_party/bfcl_eval/`, BFCL tests and BFCL-specific retrieval data (history stays in git)

**Exit:** the stock CodeAgent solves at least one dev task end to end and is scored by our scorer; the demo is live on DABstep.

## Phase B: Baseline + local labeled set (Weeks 4–6)

- [ ] **Pilot:** baseline on the 10 dev tasks → measure tokens per task, calls, failure categories, `request_too_large` rate
- [ ] **Local labeled set:** pick ~40 tasks from `all.jsonl`, stratified by level and question type, with a fixed seed. Solve each yourself in pandas in `eval/labels/` notebooks or scripts, recording the method and every manual rule used; a second pass re-checks 25%.
  - This is how you learn the domain, and it is interview material.
  - Never use public submissions or task scores.
- [ ] Freeze `eval/tasks/frozen_local.jsonl` (excludes dev tasks and demo presets)
- [ ] Run the baseline on the frozen set; `eval/analyze.py` gives accuracy with 95% bootstrap CIs, by level, plus tokens, calls and latency
- [ ] Noise check: the baseline twice on ~5 tasks

**Exit:** a publishable baseline table on the local set.

## ⏸ Exam buffer (2 weeks)

## Phase C: C1, context retrieval + token budget (Weeks 7–8)

- [ ] Split `manual.md` into sections; build cards for each column (`payments-readme.md`) and each fee-rule field
- [ ] BM25 retrieval (inherited `agent/retrieval/bm25.py`) of the top-k sections + cards per step, with a core prior (always-needed definitions), learned on dev only
- [ ] History trimming under a per-request token budget (port from `lean_agent.py`)
- [ ] Offline check (zero LLM calls): does retrieval cover the manual sections your own labeled solutions used? (coverage@k)
- [ ] Ablations: k ∈ {2, 4, 8}; full manual vs retrieved; with vs without column cards
- [ ] Run **+C1** on the frozen local set; ship a "tokens saved" counter to the demo

**Metrics:** prompt tokens per call and per task, accuracy, tasks per day on a fixed quota, `request_too_large` rate.

## Phase D: C2, code validation + repair + answer format (Weeks 9–10)

- [ ] Pre-execution checks on generated code: referenced columns exist, file paths are allowed, imports are allow-listed
- [ ] Runtime-error repair: `KeyError` → list close valid columns; empty results → hint the filter values that exist (e.g. merchant names); type and units hints; capped retries
- [ ] Answer-format validator driven by each task's `guidelines` (country code only, `X. Y` choice form, rounding, lists, "Not Applicable")
- [ ] Reuse provider-error recovery from `agent/repair.py` (HTTP 400 → feedback instead of fatal)
- [ ] Failure taxonomy per task: code_error / wrong_column / empty_result / format_fail / wrong_answer
- [ ] Run **+C1+C2**

**Metrics:** code-error rate, repairs, format failures, accuracy.

## Phase E: C5, quota-aware provider router (Week 11)

- [ ] Per-model RPM/TPM/RPD/TPD tracking in Redis
- [ ] Route Groq `gpt-oss-120b` → `qwen3.8-27b` → `gpt-oss-20b` → Gemini (AI Studio) → GitHub Models; fail over on 429/5xx/timeouts with backoff
- [ ] Load test with simulated concurrent demo visitors

**Metrics:** request success under load, with vs without the router.

## Phase F: C3, analysis-template caching (Weeks 12–14)

- [ ] After a correct solve, extract a template: question shape → steps / code skeleton with slots (merchant, period, card scheme, rule ID)
- [ ] For a new question, retrieve similar templates and let the LLM fill the slots and adapt them; validate the result through C2
- [ ] Reuse guard: fall back to full reasoning if slot-filling fails or the result is empty
- [ ] Warm-up tasks disjoint from test tasks
- [ ] Run **+C1+C2+C3**; add a "template reused" badge to the demo

**Metrics:** LLM calls and tokens per task, latency, accuracy retained, cache hit rate.

## Phase G: C4, multi-agent study (Weeks 15–16)

- [ ] Planner (reads the manual, writes the analysis plan) → analyst (writes and runs code) → reviewer (checks the answer against the manual and guidelines), via smolagents managed agents
- [ ] Compare with the best single-agent config **at an equal token budget**; report it honestly
- [ ] Add a single/multi toggle to the demo

## Phase H: Full evaluation + leaderboard (Weeks 17–19)

- [ ] Re-run all configs on the frozen local set; final table with CIs, McNemar's test, ablations, failure analysis
- [ ] Plan the official submissions within quota. Full 450-task runs take many days of free quota, so run them overnight across providers.
  - Submit **Baseline** and the **best config** only.
  - Record the scores and leaderboard rank with dates.
- [ ] Record 10–15 showcase runs for the demo's replay mode

**Exit:** every resume placeholder is filled with a measured number.

## Phase I: Polish, docs, resume (Weeks 20–21)

- [ ] Results dashboard page on the live site (local results + leaderboard scores)
- [ ] "Business insight" view in the demo: answer + chart + a 2–3 sentence explanation citing the manual section used
- [ ] README: problem, architecture, **Original vs Our Contribution**, results, attribution
- [ ] Report, slides, a 2-minute demo video, resume bullets, a 90-second pitch

## Future scope

- [ ] Free-form "ask your own question" mode with strict limits (no expected answer; show the code and an evidence table)
- [ ] CI jobs that use API keys (repository secrets; manual dispatch only)
- [ ] Text-to-SQL backend (DuckDB) as an alternative executor; compare with pandas

---

## Timeline summary

| Weeks | Phase | Live demo shows |
|---|---|---|
| 1–3 | A: Pivot to DABstep | Stock CodeAgent on business questions |
| 4–6 | B: Baseline + local labeled set | same |
| — | Exam buffer | same |
| 7–8 | C: C1 Context retrieval | tokens-saved counter |
| 9–10 | D: C2 Validate & repair | repaired-code markers |
| 11 | E: C5 Router | stays up under load |
| 12–14 | F: C3 Template cache | template-reused badge |
| 15–16 | G: C4 Multi-agent | single/multi toggle |
| 17–19 | H: Evaluation + leaderboard | replay mode |
| 20–21 | I: Polish | results dashboard, insight view |

## Risks

| Risk | Mitigation |
|---|---|
| Only 10 labeled dev tasks | Build our own ~40-task labeled set (Phase B); it doubles as domain learning |
| Full 450-task submissions are quota-heavy | C1 first; overnight runs across Groq models + Gemini; only 2 planned submissions |
| Leaderboard rules (verified A1): all 450 required, HF login, one submission per org-agent name, results public | Plan Phase H around unique agent names; only finished configs |
| LLM-written code in a public demo | Restricted executor, allow-listed imports, read-only data, hardening tests (A3), step caps |
| Vercel bundle or cold start with pandas + 23.6 MB CSV | Measure in A4; convert to a compact format at build time if needed |
| Hard tasks remain hard (low absolute accuracy) | Report relative gains with CIs and per-category analysis; easy-set accuracy and token savings are also results |
| Two projects in parallel | Phases are independent after B; C4 can be dropped without breaking the story |

## Resume template (fill in after Phase H)

**Lean Analyst: GenAI Data-Analyst Agent for Business Analytics** · [Live Demo] · [GitHub]
*Python, smolagents, pandas, Groq, FastAPI, Next.js, Vercel, Redis*

- Built a code-writing analyst agent on Hugging Face smolagents for Adyen's DABstep payments-analytics benchmark, scoring [X]% on the official leaderboard ([Y]% on hard tasks) at ₹0 inference cost.
- Cut prompt tokens per step by [X]% with BM25 retrieval over the business manual and data-schema cards, raising tasks completed per day on a free API quota by [Y]×.
- Added pre-execution code validation, runtime-error repair and guideline-driven answer formatting, reducing code errors by [X]% and raising accuracy from [A]% to [B]%.
- Implemented analysis-template caching and a quota-aware multi-provider LLM router, cutting LLM calls per question by [X]%; deployed a live demo with sandboxed execution, rate limits and replay fallback.
