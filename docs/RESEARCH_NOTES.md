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
| Submission | Answers submitted on the leaderboard Space (https://huggingface.co/spaces/adyen/DABstep) and graded instantly; baseline code (`run.py`) lives in the Space. **Unverified:** whether all 450 are required, submission limits, scorer license | HF blog; Space page didn't render details |
| Baselines | Hard set: best agents below 20% (o3-mini 16%, Claude Sonnet 12%, DeepSeek V3 ~6%); the paper reports 14.55% best on hard. Easy set: Llama 70B zero-shot can exceed 90% (per blog) | HF blog, paper |
| ⚠ Leakage | The dataset also publishes `data/submissions/*.jsonl` (2,268 files) and `data/task_scores/*.jsonl`. Hidden answers could be reconstructed from them. **Do not use** (project rule) | HF API listing |

**Example dev tasks:**
- "Which issuing country has the highest number of transactions?" → `NL` (easy)
- "Is Martinis_Fine_Steakhouse in danger of getting a high-fraud rate fine?" → `Not Applicable` (easy)

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
