# Research Notes

Facts verified on **2026-10-04** (Lean Agents selection) and **2026-10-12** (Lean Analyst / DABstep). Free tiers change often, so re-check each one before relying on it.

## DABstep (verified 2026-10-12)

| Item | Fact | Source |
|---|---|---|
| What | Data Agent Benchmark for Multi-step Reasoning, by Adyen + Hugging Face; tasks derived from Adyen's operational analytics | [paper](https://arxiv.org/abs/2506.23719), [HF blog](https://huggingface.co/blog/dabstep), [Adyen](https://www.adyen.com/knowledge-hub/data-agent-benchmark-for-multi-step-reasoning-dabstep) |
| License | Dataset **CC BY 4.0** (HF dataset card tag) | https://huggingface.co/datasets/adyen/DABstep |
| Tasks | `data/tasks/all.jsonl`: **450** tasks (72 easy, 378 hard), **answers empty**. `data/tasks/dev.jsonl`: **10** tasks (3 easy, 7 hard) with answers. Fields: `task_id`, `question`, `guidelines`, `level`, `answer` | dataset files (HF API, last modified 2026-10-11) |
| Context files | `payments.csv` 23,581,339 B; `fees.json` 531,118 B; `manual.md` 22,127 B (~5.5K tokens at ~4 chars/token); `merchant_category_codes.csv` 26,611 B; `merchant_data.json` 6,857 B; `payments-readme.md` 1,719 B; `acquirer_countries.csv` 194 B | HF API tree listing |
| `payments.csv` columns | psp_reference, merchant, card_scheme, year, hour_of_day, minute_of_hour, day_of_year, is_credit, eur_amount, ip_country, issuing_country, device_type, ip_address, email_address, card_number, shopper_interaction, card_bin, has_fraudulent_dispute, is_refused_by_adyen, aci, acquirer_country | file header |
| Scoring | Binary per task. Numbers compared with adaptive tolerance; strings normalized + fuzzy-matched against a threshold; lists element-wise | HF blog |
| Submission | Answers submitted on the leaderboard Space (https://huggingface.co/spaces/adyen/DABstep) and graded instantly; baseline code (`run.py`) lives in the Space. See "Leaderboard Space" below (verified A1) | Space source |
| Baselines | Hard set: best agents below 20% (o3-mini 16%, Claude Sonnet 12%, DeepSeek V3 ~6%); the paper reports 14.55% best on hard. Easy set: Llama 70B zero-shot can exceed 90% (per blog) | HF blog, paper |
| ⚠ Leakage | The dataset also publishes `data/submissions/*.jsonl` (2,268 files) and `data/task_scores/*.jsonl`. Hidden answers could be reconstructed from them. **Do not use** (project rule) | HF API listing |

**Example dev tasks:**
- "Which issuing country has the highest number of transactions?" → `NL` (easy)
- "Is Martinis_Fine_Steakhouse in danger of getting a high-fraud rate fine?" → `Not Applicable` (easy)

### Pinned download (Phase A1, 2026-10-12)

Dataset `adyen/DABstep` at revision **`cebda164a72ed62e210f8e576049384830141d57`**, downloaded to
`data/dabstep/` (gitignored); `data/dabstep/MANIFEST.json` holds the full list. Only context files,
`tasks/*.jsonl`, `LICENSE` and `README.md` were downloaded, never `submissions/` or `task_scores/`.

| File | SHA-256 |
|---|---|
| `context/payments.csv` | `5fbb26210a45427d7a6560cfab3a362a08e4067f27cd03695f211a51c47ffc25` |
| `context/fees.json` | `9a833666ae9be5a8e756dd1fe076c72e7c502d64161315ffa8fee9e5bf2599dc` |
| `context/manual.md` | `bb7f4ca6fdc759af1f480702b3a3b12e17e9293b0d38a1dbfbbc8ffc1e572d2c` |
| `context/merchant_data.json` | `f158e834de27ee8407e99d9c32da690357981d2770958fd302a9bb79ced83581` |
| `context/merchant_category_codes.csv` | `83247d79f5ddcdd180e02f184b644f4912731942a2fc58d91f2a06b911d04b41` |
| `context/payments-readme.md` | `8754b92d0b3127856ff72266ea482995d2a1f6a34d0a12732f7c26f527f2c4a5` |
| `context/acquirer_countries.csv` | `6744cf1962e4b5086342821e627f4557c32f06c3c58e8b0ff3b449dcc634f37f` |
| `tasks/all.jsonl` | `d776385abe09ff89ed3263bd47c90fa0f060680c0d2ef04a83485fa4b6f2512c` |
| `tasks/dev.jsonl` | `c1da755a6fe9cb538fc84719f51e1db0bff0190a1d6905767ac18c755e66a07b` |

Confirmed on download: `all.jsonl` 450 rows, every `answer` empty; `dev.jsonl` 10 rows, all answered.

### Leaderboard Space (read 2026-10-12, Space revision `d4431c2e`)

Source: `app.py`, `dabstep_benchmark/{leaderboard,utils,content}.py`, `evaluation/scorer.py`, `baseline/`.

| Question | Answer |
|---|---|
| All 450 answers required? | **Yes.** `evaluate()` loops over every hidden task and raises `KeyError` ("Task ID … not found") if any is missing, so a partial file is rejected |
| Format | JSONL with mandatory `task_id`, `agent_answer`; optional `reasoning_trace`. Any other column → rejected. All values must be strings, no NaN |
| HF login needed? | **Yes.** The submit handler takes a `gr.OAuthProfile` (Gradio `LoginButton`); also asks for agent name, organisation, email, model family, optional repo URL |
| Submission limits | No rate limit in code, but **each `organisation-agent_name` pair can be submitted only once**. The file and per-task scores are uploaded to the **public** dataset |
| Validation | Closed: the validated board takes no new entries ("DABStep-v2 launching in the coming weeks"). New submissions go to the **Unvalidated** board |
| Scorer license | Space is **CC BY 4.0** (README front matter + LICENSE). Vendoring `scorer.py` is allowed with attribution |
| Scorer rules | Lowercase + strip. If either side is a comma-thousands number or plain decimal → numeric compare. Else if `,` or `;` present → list compare (brackets stripped, sorted, item-wise recursive). Else numeric if both contain a number (first number extracted). Else strings: equal after stripping non-word chars, or single-word subset, or `SequenceMatcher` ratio > 0.95. Numeric: equal, or both < 1 → `isclose(1e-4)`, else round both to the fewer decimal places, else `isclose(rel 1e-4)` |
| Baseline | smolagents **1.3.0** `CodeAgent` via LiteLLM, `max_steps=10`, authorized imports `numpy, pandas, json, csv, glob, markdown, os`; the agent explores the context directory itself (manual not pre-loaded); "Not Applicable" when no answer |

Scorer quirks worth knowing (they affect C2 answer formatting): a scalar answer containing a comma is
treated as a list; the "first number" rule means `"12 transactions"` matches `"12"`; rounding both to the
fewer decimal places means a coarser answer can still match (truth `3.14159` vs `3.14` → equal at 2 dp),
but a wrongly rounded one fails (`3.15`).

### Other business-analytics benchmarks considered

- **InsightBench** (ServiceNow; code MIT, data CC BY 4.0): end-to-end insight generation; scored by an LLM judge. https://github.com/ServiceNow/insight-bench
- **BIRD Mini-Dev** (text-to-SQL): 500 questions; a VLDB 2026 analysis found annotation errors in 52.8% of Mini-Dev problems. https://www.vldb.org/cidrdb/papers/2026/p5-jin.pdf
- **"Agent Bain vs. Agent McKinsey"** (business-domain text-to-SQL, 2025): https://arxiv.org/pdf/2510.07309 (license/status not verified)

---

## Inherited from Lean Agents (2026-10-04)

## Foundations

| Repo | License | Notes (as of 2026-10-04) |
|---|---|---|
| [huggingface/smolagents](https://github.com/huggingface/smolagents) | Apache-2.0 | ~29.7k★, last push 2026-09-30. `agents.py` <1,000 LOC. `ToolCallingAgent`, `CodeAgent`, managed agents. Backends include LiteLLM / OpenAI-compatible endpoints / Ollama. Has `examples/smolagents_benchmark/`. |
| [ShishirPatil/gorilla (BFCL)](https://github.com/ShishirPatil/gorilla/tree/main/berkeley-function-call-leaderboard) | Apache-2.0 | BFCL v4. Multi-turn tasks use local simulated Python APIs in `bfcl_eval/eval_checker/multi_turn_eval/func_source_code/`. Supports OpenAI-compatible endpoints (`--skip-server-setup`, `LOCAL_SERVER_ENDPOINT`/`LOCAL_SERVER_PORT`). The web-search category needs SerpAPI, so skip it. |

Simulated API files: `gorilla_file_system.py`, `math_api.py`, `message_api.py`, `posting_api.py`, `ticket_api.py`, `trading_bot.py`, `travel_booking.py`, `vehicle_control.py`, `long_context.py`, `memory_kv.py`, `memory_vector.py`, `memory_rec_sum.py`, `memory_api_metaclass.py`, `web_search.py`.

## Free tiers

| Service | Limits | Source |
|---|---|---|
| Groq | Free models include `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`: 30 RPM, 1K RPD, 8K TPM, 200K TPD **per model**. Llama models are no longer on the free list. | https://console.groq.com/docs/rate-limits |
| ~~Cerebras~~ **Rejected** | **Requires a payment card** to activate API access (seen on its console, 2026-10-04). Its one-time $5 credit expires after 30 days, then access pauses. Third-party "no card" claims were wrong. | Cerebras console |
| Google AI Studio (Gemini) | No card; key needs only a Google account. Flash/Flash-Lite models with function calling. Per-project RPM/TPM/RPD; resets midnight Pacific; tightened in 2026 and not guaranteed. OpenAI-compatible endpoint. | https://aireiter.com/blog/google-ai-studio-free-api · https://ai.google.dev/gemini-api/docs/function-calling |
| GitHub Models | Free with a GitHub account. Low-tier models (e.g. gpt-4o-mini): 15 RPM / 150 RPD; high-tier: 10 RPM / 50 RPD; **8K input tokens per request** | https://getaitools.dev/service/github-models |
| OpenRouter `:free` models | 20 RPM, **50 requests/day** without $10 of purchased credit. Last resort only. | https://klymentiev.com/blog/openrouter-free-tier |
| Vercel Hobby | Python functions; 300 s max duration (Fluid compute); 2 GB / 1 vCPU; 500 MB Python bundle; 4.5 MB request/response body; non-commercial use | https://vercel.com/docs/functions/limitations |
| Upstash Redis | 500K commands/month, 256 MB data, 10 GB bandwidth | https://upstash.com/blog/redis-new-pricing |
| Gemini API | Free tier tightened in 2026; quotas per project, not guaranteed | https://www.memetik.ai/guides/gemini-api-free-tier-limits |
| HF Spaces | New free accounts can no longer create Docker/Gradio CPU Spaces (static only). Not used. | https://discuss.huggingface.co/t/official-community-complaint-revert-free-cpu-basic-spaces-and-remove-anti-developer-sdk-restrictions/177703 |

## Local dev machine (measured)

- Hardware: i5-1235U, 8 GB RAM, Intel Iris Xe (no CUDA), Ollama 0.34.4.
- Measured on an 800-token agent prompt with 15 tool definitions:

| Model | Prompt reading | Generation | Total |
|---|---|---|---|
| `qwen2.5:3b-instruct` | ~47 tok/s | ~12 tok/s | ~26 s |
| `qwen2.5:7b-instruct` | ~6 tok/s | 0.3 tok/s | 331 s (memory swapping; unusable) |

- Project rule: don't run local models by default. Use hosted free tiers; fall back to a local model only when really necessary.

## Papers to read / cite

- **Agentic Plan Caching** (NeurIPS 2025): https://arxiv.org/abs/2506.14852. The basis for C3. Reimplement from the paper; don't copy code without checking its license.
- **Workload-Aware Caching for Multi-Agent Systems** (2026): https://arxiv.org/pdf/2607.20495
- **Small Language Models for Agentic Systems** (survey): https://arxiv.org/pdf/2510.03847
- **Invocation-Level Reliability of Tool-Using Agents** (2026): https://arxiv.org/pdf/2608.26189. Relevant to C2.
- **Structured Reflection for Reliable Tool Interactions**: https://arxiv.org/html/2509.18847. Relevant to C2.
- **Callability Is Not Operability** (2026): https://arxiv.org/pdf/2608.23628
- **The Double Measurement Confound in Agent Benchmarks** (2026): https://arxiv.org/pdf/2609.09218. Read before designing the evaluation.

## Alternatives considered (not chosen)

- **GPTCache verified semantic caching** (MIT). A strong ML + LLM systems project, with a new 1,536-case reuse benchmark (Sep 2026). Not chosen because it isn't agentic.
- **OSV-Scanner Python reachability**. Ambitious security project.
- **Asynq fair scheduling**. Safe backend project.
