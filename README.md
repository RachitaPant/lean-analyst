# Lean Analyst

**A token-efficient, reliable GenAI data-analyst agent for business analytics on free-tier LLMs.**

> Status: 🔀 **Pivot in progress.** Forked from [Lean Agents](https://github.com/RachitaPant/Lean-Agents) (BFCL tool-calling agents) and being retargeted to **DABstep**, a business-analytics benchmark. See [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) and the [phase log](docs/PHASE_LOG.md).
>
> Live demo: _Phase A_ · Leaderboard result: _after the first official submission_

---

## The problem

Businesses want to ask questions of their data in plain English:
- "Which merchant would pay the most in fees if…"
- "What is our fraud rate on card scheme X in Q3?"
- "Is merchant Y at risk of a high-fraud fine?"

A useful GenAI analyst has to read a long **business manual** (fee rules, fraud policy, definitions), combine it with **structured data** (payments, fee tables, merchant records), write and run analysis code over several steps, and return an exact answer.

Current agents are bad at this:
1. **Accuracy is low.** On DABstep, the best agents reported by its authors stayed below 20% on hard tasks ([HF blog](https://huggingface.co/blog/dabstep); 14.55% in the [paper](https://arxiv.org/abs/2506.23719)).
2. **They waste tokens.** The business manual alone is ~22 KB (~5.5K tokens). Sending it plus the data schemas every step does not fit a free tier (Groq: 8K tokens/minute, 200K/day per model).
3. **Their generated code breaks.** Wrong column names, wrong joins, misread fee rules and badly formatted answers make the task fail even when the reasoning is close.
4. **They re-derive the same analysis.** Many hard tasks share one shape ("fees for merchant X in period Y under rule Z"), but agents start from scratch every time.
5. **They are fragile.** A single provider's rate limit or outage stops the analysis.

**Goal:** answer more business-analytics questions correctly with fewer tokens and LLM calls, at ₹0, and **prove every improvement with numbers**: a local labeled set plus the official DABstep leaderboard.

## What already exists vs. what this project adds

| Existing (foundation) | This project's contribution |
|---|---|
| [smolagents](https://github.com/huggingface/smolagents) (Hugging Face, Apache-2.0): `CodeAgent` + sandboxed `LocalPythonExecutor`, managed agents | **C1: Context retrieval + token budget.** Send only the relevant manual sections, column cards and fee-rule fields each step; trim history |
| [DABstep](https://huggingface.co/datasets/adyen/DABstep) (Adyen + Hugging Face, CC BY 4.0): 450 real payments-analytics tasks, data files, public leaderboard | **C2: Validate-and-repair for analysis code.** Pre-execution checks (allowed files, columns, imports), targeted feedback on runtime errors, answer-format checks against each task's guidelines |
| Inherited from Lean Agents: streaming runner, eval harness, Upstash guard, Next.js trace UI, provider error handling | **C3: Analysis-template caching.** Reuse solved analysis plans for structurally similar questions |
| Groq / Gemini / GitHub Models free-tier LLM APIs | **C4: Multi-agent study.** Planner → analyst → reviewer vs. single agent at an equal token budget |
| | **C5: Quota-aware provider router.** Per-model RPM/TPM/TPD tracking and failover |
| | Business-analytics demo: ask a question, then watch the agent read the manual, write pandas, show a chart and explain the answer |

## Architecture

```
                 Visitor opens link (one click)
                              │
        ┌─────────────────────▼──────────────────────┐
        │  Next.js frontend  (Vercel Hobby)          │
        │  • pick a business question                │
        │  • live trace: manual sections read, code, │
        │    results, chart, final answer            │
        │  • baseline vs improved; results dashboard │
        └─────────────────────┬──────────────────────┘
                              │ streamed steps (NDJSON)
        ┌─────────────────────▼──────────────────────┐
        │  FastAPI /api/run  (Vercel Python service) │
        │  smolagents CodeAgent, extended with:      │
        │   C1 Manual/schema retrieval + budget      │
        │   C2 Code validation + repair + answer fmt │
        │   C3 Analysis-template cache               │
        │   C4 Planner / Analyst / Reviewer          │
        │   C5 Provider router (quota-aware)         │
        │  Executor: restricted LocalPythonExecutor  │
        │  Data: DABstep context files (read-only)   │
        └───────┬────────────────────────┬───────────┘
                │                        │
   ┌────────────▼──────────┐   ┌─────────▼──────────────────┐
   │ Upstash Redis (free)  │   │ LLM APIs (free tiers)      │
   │ • template cache      │   │ Groq gpt-oss-120b / qwen   │
   │ • rate limit / budget │   │ → Gemini → GitHub Models   │
   │ • recorded replays    │   └────────────────────────────┘
   └───────────────────────┘
```

Public-demo safety:
- **Restricted code execution.** smolagents' AST-interpreting executor runs only allow-listed imports (pandas, numpy, …), reads only the bundled data files, and has no network access. It is hardened and tested in Phase A.
- **Quota protection.** Per-visitor rate limits plus a daily token budget.
- **Replay fallback.** When the budget is spent, the site replays recorded runs.

## The data (DABstep context files)

| File | Size | Contents |
|---|---|---|
| `payments.csv` | 23.6 MB | Transactions: merchant, card scheme, amount, countries, device, fraud dispute, refusal, ACI… |
| `fees.json` | 531 KB | Fee rules (conditions → fixed + rate) |
| `manual.md` | 22 KB | The business manual: fee logic, fraud and fines policy, definitions |
| `merchant_data.json` | 7 KB | Merchant attributes (account type, MCC, acquirers, capture delay) |
| `merchant_category_codes.csv`, `acquirer_countries.csv`, `payments-readme.md` | small | Lookups and column docs |

Tasks: **450** (72 easy, 378 hard), answers hidden and scored by the leaderboard; **10 dev tasks** with answers. Scoring is binary per task, with numeric tolerance and fuzzy string matching.

## Tech stack (all ₹0)

| Layer | Choice |
|---|---|
| Agent framework | smolagents `CodeAgent` (Apache-2.0) |
| Benchmark + data | DABstep (CC BY 4.0) |
| Analysis | pandas, NumPy (inside the restricted executor) |
| LLMs | Groq free tier (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`); fallbacks: Gemini (AI Studio), GitHub Models. All without a card. |
| Retrieval (C1) | Dependency-free BM25 (inherited) over manual sections + column/field cards |
| Cache, rate limit, budget | Upstash Redis (free tier) |
| Backend | FastAPI as a Vercel Python service (streaming) |
| Frontend | Next.js + TypeScript + Tailwind + Recharts |
| Evaluation | pandas, NumPy/SciPy (bootstrap CIs), matplotlib |
| Testing / CI | pytest, GitHub Actions |

## Evaluation

| Config | Description |
|---|---|
| Baseline | Stock smolagents `CodeAgent`, full manual in the prompt (the DABstep-style baseline) |
| +C1 | Context retrieval + token budget |
| +C1+C2 | + code validation, repair, answer formatting |
| +C1+C2+C3 | + analysis-template caching |
| C4 | Multi-agent variant at an equal token budget |

Three evaluation layers:
1. **Dev set (10 tasks, labeled):** pipeline checks and quick iteration.
2. **Local labeled set (~40 tasks):** tasks from the public 450 that we label ourselves by solving them in pandas, with the method recorded. Frozen once built; used for all config comparisons.
3. **Official leaderboard:** full 450-task submissions for the headline number (few, because of quota).

**Metrics:** accuracy (easy/hard), tokens and LLM calls per task, latency, code-error rate, repairs, cache hit rate, tasks completed per day on a fixed free quota. 95% bootstrap CIs; McNemar's test across configs on the same tasks.

No results are reported until they are measured.

## Repository layout

```
agent/        core: runner.py (shared loop, streams trace events), lean_agent.py, repair.py,
              retrieval/ (BM25); DABstep adapter added in Phase A
server/       FastAPI demo API (Vercel Python service at /api): app.py, guard.py
web/          Next.js + TS + Tailwind frontend (Vercel service at /)
eval/         run.py, analyze.py, configs.py, make_tasks.py, tasks/, results/
third_party/  vendored code/data with license notices (BFCL subset, removed in Phase A)
docs/         plan, phase log, research notes, architecture notes
```

## Getting started (dev)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env           # add GROQ_API_KEY, Upstash, etc.
```

## Attribution

- **smolagents** © Hugging Face, Apache License 2.0.
- **DABstep** dataset © Adyen / Hugging Face, CC BY 4.0. Context files and tasks are used with attribution; any derived files are marked.
- Code inherited from **Lean Agents** (same author).
- Ideas reimplemented from papers are cited in [docs/RESEARCH_NOTES.md](docs/RESEARCH_NOTES.md).
