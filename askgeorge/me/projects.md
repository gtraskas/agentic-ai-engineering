# Georgios Traskas — Project Portfolio (Deep Dive)

## MolekitChen — RAG iOS App (2026, live on App Store)

Full-stack food-science Q&A app answering cooking questions with citations from peer-reviewed research (CC0/CC-BY papers, USDA, PubChem).

**Stack:** Python, FastAPI, Supabase (PostgreSQL + pgvector HNSW), Google Gemini, LangChain, Swift/SwiftUI, Render, GitHub Actions.

**Key decisions:**
- Hybrid retrieval (BM25 + vector + Reciprocal Rank Fusion): BM25 catches exact terms like "citric acid"; vector search catches "sour compound" semantically.
- Deterministic USDA layer: for nutrient-retention questions, intent is detected with regex and the USDA table value is injected verbatim — the LLM never invents numbers.
- Five-layer deterministic guardrail stack (gibberish, prompt injection, SQL injection, medical scope, language) plus an output sanitizer — regex-based, fast, predictable.
- Pydantic output contracts with a repair loop (up to 3 re-prompts) before a safe fallback.

**Impact:** Live on App Store, 1,600+ indexed papers, sub-50ms retrieval, free/pro tiers via StoreKit.

**More key decisions:**

- **Hard token budget:** max 7,000 input tokens with 1,400 reserved for fixed prompt overhead; chunks are trimmed lowest-score-first when the assembled context would overflow, never the top results, always keeping a minimum grounding floor.
- **Evaluation gate:** a golden dataset of 50+ real questions with verified answers, scored by LLM-as-a-judge on faithfulness, relevance, and context precision after every change — deployment is blocked if any metric drops.
- **Model fallback chain:** if the primary model returns errors or rate limits, the same prompt routes to a backup provider; exact model checkpoints are pinned, never aliases.
- **In-database vector search (RPCs):** similarity search runs as a SQL function inside Postgres — one round trip, and Row-Level Security is enforced at the database engine, not in application code.
- **Food Resolver:** free-text ingredient names map to canonical USDA food IDs with confidence thresholds, manual overrides (e.g. "rocket" → arugula), and graceful skips — so messy user input never crashes the pipeline.
- **Multi-layer rate limiting:** per-user/IP request caps, database-backed daily quotas, and burst protection, plus exponential backoff with jitter on upstream API calls.

**Q&A — "How do you prevent hallucinations?"** Layers: retrieval quality first, deterministic USDA injection for exact numbers, Pydantic output contracts, citation validation (cited indices must exist), output sanitizer strips medical claims.
**Q&A — "Why pgvector over Pinecone?"** Cost (free with existing Supabase), SQL joins in the same query, full RLS control. At 1,600 papers performance is identical; a migration path exists.
**Q&A — "Hardest part?"** Citation renumbering after merging chunks + structured evidence + LLM output — sequential renumbering, dropping uncited sources, verifying integrity without changing meaning.

## Wine-VFM — Autonomous Multi-Agent Bargain Hunter (2026, live demo)

Agentic AI that hunts wine bargains: estimates value-for-money (0-99) from tasting notes using three heterogeneous models under an LLM planner, scans a real online wine shop, and pushes an alert when price beats profile.
Live demo: https://gtraskas--wine-vfm-app-web.modal.run (first load ~30s) | Code: https://github.com/gtraskas/wine-vfm

**Stack:** Python, Modal (serverless GPU), fine-tuned Llama 3.2 3B (QLoRA 4-bit, rank-256), OpenAI frontier models, ChromaDB, PyTorch, Scikit-learn, Gradio, Pushover, uv, HuggingFace Hub.

**Key decisions:**
- Deterministic VFM target: a fixed formula over critic points and price — ground truth stays out of the model's hands.
- Three heterogeneous estimators + fitted ensemble: fine-tuned Llama specialist on Modal GPU; RAG estimator (ChromaDB over ~88K embedded tasting notes feeding a frontier LLM); bag-of-words neural network. Ensemble weights fitted by linear regression on 200 validation wines, evaluated with MAE/R².
- Two planners: a deterministic plain-code baseline and an autonomous LLM planner given scan/estimate/notify as tools — the model doesn't know its tools are agents.
- Serverless economics: CPU web app scales to zero; GPU wakes only during a hunt; artifacts and memory persist on a Modal Volume.
- Autonomy and memory: remembers past finds, runs in the background, reaches out proactively via push notifications.

**The agent roster (8 agents):** SpecialistAgent (fine-tuned Llama on Modal GPU), FrontierAgent (RAG over the vector store feeding a frontier model), NeuralNetworkAgent (local bag-of-words network), EnsembleAgent (regression-fitted blend), ScannerAgent (live shop listings, structured extraction of the best-documented wines), MessagingAgent (push notifications), PlanningAgent (plain-code orchestrator baseline), AutonomousPlanningAgent (LLM planner given scan/estimate/notify as tools — it does not know its tools are agents).

**Q&A — "What makes this agentic rather than a pipeline?"** The planner is an LLM with tools, looping toward a goal, deciding what happens when; the tools it calls are themselves agents. Structured outputs, shared environment, persistence, proactive outreach. The plain-code baseline shows exactly what the LLM planner adds — and costs.
**Q&A — "Why an ensemble?"** The three models fail differently: the specialist is deep but frozen; RAG stays current with the vectorstore; the neural net is a cheap sanity anchor. Regression-fitted weights let validation data decide trust.

## Predictive Fitness — MCP Server (2026)

MCP server letting AI agents fetch athlete data and act for real users, instead of one integration per client. Python PoC (stdio, direct AWS DB over VPN) accepted and ported to TypeScript production (Streamable HTTP, Prisma over GraphQL, RAG layer for training-metric knowledge, ~15 tools).

**Key insight — tool selection at scale:** as tools grew, models treated the first batch of tool-search results as the whole toolkit and silently called the wrong tool; users got wrong charts or nothing although the right tool existed. Fix: unambiguous tool naming/descriptions plus a golden query set (with known-correct tool per query, tested across AI clients including low-reasoning ones) gating every new tool.

## Predictive Fitness — Causal Scoring Pipeline (2026)

Production daily pipeline estimating causal effects of in-trial actions on 30-day trial-to-paid conversion for athlete coaching apps. Output: per-user conversion probability, per-treatment uplift with 95% CIs, what-if scenarios for marketing.

**Stack:** Python, EconML (LinearDML), DoWhy, HistGradientBoosting, Scikit-learn, Streamlit, MySQL.

**Key decisions:** Double Machine Learning to partial out confounders (Chernozhukov et al. 2018); DAG-derived adjustment sets via DoWhy's backdoor criterion (never conditioning on mediators); GBM nuisances + linear final stage for smooth heterogeneous effects with closed-form CIs; Baron & Kenny mediator analysis showed ~76% of device effect flowed through sessions — marketing now nudges device + sessions together.
Validation: refutation tests (random common cause, placebo treatment, subset stability) all passed. Probabilities are Platt-calibrated so a predicted 70% means 70% in reality, and positivity (treatment overlap) is checked per treatment — levers with poor overlap are flagged or excluded from the actionable list rather than reported with false confidence.

## Predictive Fitness — Production Alerting Redesign (2022-2026)

The monitoring system originally used static thresholds on wearable-driven pipelines whose data varies naturally by season, training cycle, and device type — producing dozens of daily false positives and complete alert fatigue. George redesigned it around a few principles (outcome: >90% reduction in alert noise, from dozens of false positives daily to a handful of genuine alerts per week):

- **Dynamic, seasonal baselines:** traffic is compared to the same weekday and hour in prior weeks, not to a global average.
- **Different windows for different volumes:** high-volume jobs get tight rolling windows; rarely-running jobs are judged over longer windows against long-term history, because one failure in two runs is statistically meaningless.
- **Evidence gates:** an alert may only fire after a minimum number of runs and distinct failures — statistical significance before paging a human.
- **Infrastructure vs algorithm separation:** a container crash and a mathematical edge case look identical in a naive error count but need different responders; tracking them separately (including a job-status vs in-record dimensions-status distinction) tells the team instantly whether to restart infrastructure or fix the algorithm.
- **Relative-spike policies for naturally noisy modules:** components with structurally high baseline failure rates alert only on large jumps above their own baseline, not on absolute rates.

## Predictive Fitness — Wearable Data Ingestion & Modeling Discipline (2022-2026)

- **Multi-source ingestion:** Garmin, Apple Watch, and Fitbit deliver different schemas, sampling rates, and timestamp formats; device-specific parsers normalise everything to a common intermediate schema at the edge, with resampling and gap-filling to a consistent cadence.
- **Late-arriving data:** workouts often sync hours after they happen; buffered reprocessing windows plus idempotent upserts keyed by event ID prevent double-counting, with nightly reconciliation as the backstop.
- **Leakage-free time-series validation:** strictly chronological splits with a gap between train and test periods; no user appears on both sides of a split; users with sparse history are handled by simple rules instead of overfitting a model to their noise; time-aware features ("days since last workout") over raw counts for irregular schedules.
- **Physics-respecting ML:** monotonicity constraints encode exercise-physiology relationships directly into gradient-boosted models (more training load cannot predict less recovery), predictions are clipped to physiologically valid ranges, and physiology-equation outputs are fed to the models as features — the model learns when to trust the equation.

## Syqe Medical — Audio Classification for Embedded Deployment (2019)

15-class sound classification for a medical inhaler (Israel), 4,500 WAV files, deployed on a microcontroller via TFLite quantization. MFCC/spectral features (193 per clip) beat raw waveforms; a feed-forward network beat CNN on this dataset size (F1 0.86 vs 0.60). 97% training accuracy, 86% test F1.

## French Institute of Gynaecology — Clinical Outcome Prediction (2018-2019)

IUI fertility outcome prediction, 1,633 patients, 84 variables, 8.5% positive class. Evaluation switched entirely to precision/recall/F1 with repeated stratified K-fold; three-strategy feature selection (mutual information, backward elimination, embedded tree importances) plus RFECV over 130,000 CV tests. Deployed as clinical decision support.

## Quidnet Energy — Data Pipeline Automation (USA)

Automated multi-format ingestion (CSV/DTF/TXT) with auto-detection into aligned time series; rule-based injection/flowback event detection; smart downsampling (~90% size reduction on quiet periods, full resolution near events). Eliminated a daily manual bottleneck for the analytics team.

## AskGeorge — This AI Representative (Jul 2026, live)

The assistant answering right now is itself one of George's projects: a production agentic AI system, open source at github.com/gtraskas/agentic-ai-engineering.

- Two switchable agent backends: a from-scratch streaming tool-calling loop and the OpenAI Agents SDK.
- In-memory Qdrant RAG with local FastEmbed embeddings over George's background documents.
- LLM-agnostic via OpenRouter; tools email George in real time (leads, unanswered questions).
- Input guardrail: a parallel judge LLM with a structured Pydantic verdict blocks off-topic, dangerous, and prompt-injection messages.
- Rate limiting: in-memory sliding windows (per-visitor hourly cap, global daily cap) protect the API budget.
- Job-fit analysis: a recruiter pastes a job description; a structured pipeline parses it into requirements, judges each against George's background via RAG, computes an honest overall band, synthesizes a first-person report, and runs an anti-flattery verifier — every run emails George the role and verdict.
- Gradio UI with custom theme and embedded booking calendar; serverless on Modal (scales to zero); GitHub Actions CI/CD with auto-deploy.

**Key decisions:**

- **In-memory Qdrant over a hosted vector database:** the corpus is small (a handful of markdown files) and static between deployments, and the app runs serverless with scale-to-zero — an always-on database would cost money to sit idle. Rebuilding the index in RAM at container startup takes seconds, needs zero infrastructure, and leaves nothing to operate or secure.
- **Hybrid dense + sparse retrieval:** dense embeddings catch meaning, a local BM25 sparse model catches exact terms (tool names, acronyms), fused by Qdrant — the same hybrid pattern as MolekitChen, fully local with FastEmbed.
- **Retrieval golden-set eval in CI:** ~20 recruiter-style questions each assert an expected needle in the retrieved context; any corpus or chunking change that silently breaks recall fails the build before it deploys.
- **Job-fit as a structured pipeline, not one prompt:** parse the job description into typed requirements, judge each one against retrieved evidence (concurrent calls via asyncio.gather), compute the overall band deterministically in code so a must-have gap can never read as a strong fit, then synthesize and run an anti-flattery verifier that regenerates the report if it overclaims. The pasted description is treated strictly as untrusted data — injection attempts and impossible requirements produce an honest "limited fit", never a fabricated match.
- **FastEmbed for embeddings:** runs locally inside the container (no API calls, no per-query cost, no external dependency at question time). The model (BAAI/bge-small-en-v1.5, 384 dimensions) is baked into the Docker image so cold starts skip the download.
- **Heading-aware chunking:** each chunk carries its markdown heading path (e.g. "[Wine-VFM > Key decisions]"), so retrieval matches on section context, not just body text — small custom splitter, no framework dependency.
- **OpenRouter instead of one provider:** one API for every LLM; the model is a single env var. Swapping Gemini for GPT or Llama requires no code change.
- **Two agent backends on purpose:** the from-scratch streaming tool-calling loop shows exactly what a framework abstracts (delta assembly, tool rounds, safety caps); the OpenAI Agents SDK version delivers the same behavior in a tenth of the code. Same philosophy as Wine-VFM's two planners — build the baseline, then let the abstraction earn its place.
- **Guardrail as a parallel judge:** the scope check runs concurrently with answer generation, so legitimate visitors pay no latency; the tripwire cancels generation only when the judge rejects. Reasoning-first field order in the verdict schema improves judgment quality.
- **Grounding over memory:** the model answers only from retrieved background documents; conversation memory is the browser's chat history replayed each turn — the correct stateless pattern for serverless, immune to container restarts.
- **Moderate temperature (0.7):** factual reliability comes from grounding rules and retrieval, not from freezing the sampler — a moderate temperature keeps answers natural and varied without touching the facts.

## Other Public GitHub Projects (github.com/gtraskas)

- **llm-portfolio** (2026) — Practical LLM projects: competitive intelligence analysis, multi-agent systems, RAG applications, autonomous AI solutions (Ollama, OpenAI).
- **guardrail-api** (2026) — AI hallucination guardrail audit suite (portfolio project).
- **knowledge-rag** (2025) — Domain-specific RAG knowledge base with conversational interface and source citations.
- **pdf-data-extractor** (2025) — Automated PDF data extraction tooling.
- **fake-news-detector** (2025) — Web app backed by a deployed SageMaker model.
- **spamIt**, **titanic_prediction**, **breast_cancer_prediction**, **autoML** — earlier ML fundamentals work.
