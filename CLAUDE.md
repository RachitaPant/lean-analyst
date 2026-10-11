# CLAUDE.md

Context for AI coding sessions on this repo.

## What this is

**Lean Analyst** is a B.Tech CSE final-year project (2026–27): a GenAI data-analyst agent for **business analytics**.

- It was **forked on 2026-10-12** from Lean Agents (`D:\personal_projects\multi-agent`, a separate project; don't edit it from here). It is being retargeted from BFCL to **DABstep** (Adyen + Hugging Face; 450 payments-analytics tasks; CC BY 4.0).
- It extends smolagents' **CodeAgent** with:
  - **C1** context retrieval + token budget (manual sections, column/field cards)
  - **C2** code validation + repair + answer formatting
  - **C3** analysis-template caching
  - **C4** multi-agent study
  - **C5** quota-aware provider router
- Deployed at ₹0 on Vercel + Upstash, with Groq free-tier LLMs (fallbacks: Gemini via AI Studio, GitHub Models).

Docs:
- **Plan and progress checkboxes:** `docs/PROJECT_PLAN.md`. Check the current phase there first.
- **Phase log:** `docs/PHASE_LOG.md` records, per phase, what was done, the findings and how direction changed. Update it at the end of every phase, and mid-phase when a finding changes the plan. Entries before 2026-10-12 are inherited Lean Agents history.
- **Verified facts, limits and papers:** `docs/RESEARCH_NOTES.md`.

## Hard rules

- **₹0 infrastructure.** Free tiers only, no card-required services. Confirm "no card" on the provider's own page (third-party summaries were wrong about Cerebras).
- **Never commit API keys.** Use `.env` locally and Vercel env vars in deployment.
- **Never invent results.** Resume and README numbers come only from `eval/` outputs or official leaderboard scores.
- **No answer leakage.** The DABstep HF dataset publishes other teams' submissions and per-task scores, from which hidden answers could be reconstructed. **Never use them** to label, tune or check our tasks. Local labels come only from the 10 dev answers and our own documented solutions.
- **Evaluation hygiene.**
  - Freeze the local labeled set once built, and don't tune on it.
  - Template-cache warm-up tasks must be disjoint from test tasks.
  - Don't iterate against the leaderboard. Submit only planned, finished configs.
- **Sandboxing.** LLM-written code runs only in smolagents' restricted executor, with allow-listed imports, read-only access to the bundled data files and no network. Never use `exec`/`subprocess` on model output.
- **Attribution.** smolagents is Apache-2.0; DABstep is CC BY 4.0. Keep notices and mark modified/derived files.
- Keep providers swappable via config. Free-tier limits change.
- Runtime deps go in `requirements.txt` (Vercel installs it); dev-only tools go in `requirements-dev.txt`.

## Environment

- Windows 11, 8 GB RAM, no CUDA. The `.venv` uses Python 3.11 (3.12 isn't installed).
- **No local models by default.** Use hosted free-tier APIs (Groq first). A local model only when truly necessary, and ask the user first.
- Store caches on D: (`HF_HOME=D:\hf`); C: is low on space. Download DABstep context files to `data/dabstep/` (gitignored if large; `payments.csv` is 23.6 MB).

## Layout

```
agent/        runner.py (shared agent loop, streams trace events), lean_agent.py (C1 levers),
              repair.py (C2), retrieval/ (BM25). Phase A adds dabstep.py (data, tasks, scorer)
              and a CodeAgent-based lean agent; bfcl_adapter.py is removed at the end of Phase A
server/       FastAPI demo API (Vercel Python service at /api): app.py, guard.py
web/          Next.js + TS + Tailwind frontend (Vercel service at /)
eval/         run.py, analyze.py, configs.py, make_tasks.py, tasks/, results/
third_party/  vendored BFCL subset (Apache-2.0), to be removed in Phase A
docs/         plan, phase log, research notes, architecture notes
vercel.json   Vercel Services: web/ at /, server.app:app at /api/*
```
