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

**Q&A — "What makes this agentic rather than a pipeline?"** The planner is an LLM with tools, looping toward a goal, deciding what happens when; the tools it calls are themselves agents. Structured outputs, shared environment, persistence, proactive outreach. The plain-code baseline shows exactly what the LLM planner adds — and costs.
**Q&A — "Why an ensemble?"** The three models fail differently: the specialist is deep but frozen; RAG stays current with the vectorstore; the neural net is a cheap sanity anchor. Regression-fitted weights let validation data decide trust.

## Predictive Fitness — MCP Server (2026)

MCP server letting AI agents fetch athlete data and act for real users, instead of one integration per client. Python PoC (stdio, direct AWS DB over VPN) accepted and ported to TypeScript production (Streamable HTTP, Prisma over GraphQL, RAG layer for training-metric knowledge, ~15 tools).

**Key insight — tool selection at scale:** as tools grew, models treated the first batch of tool-search results as the whole toolkit and silently called the wrong tool; users got wrong charts or nothing although the right tool existed. Fix: unambiguous tool naming/descriptions plus a golden query set (with known-correct tool per query, tested across AI clients including low-reasoning ones) gating every new tool.

## Predictive Fitness — Causal Scoring Pipeline (2022-2026)

Production daily pipeline estimating causal effects of in-trial actions on 30-day trial-to-paid conversion for athlete coaching apps. Output: per-user conversion probability, per-treatment uplift with 95% CIs, what-if scenarios for marketing.

**Stack:** Python, EconML (LinearDML), DoWhy, HistGradientBoosting, Scikit-learn, Streamlit, MySQL.

**Key decisions:** Double Machine Learning to partial out confounders (Chernozhukov et al. 2018); DAG-derived adjustment sets via DoWhy's backdoor criterion (never conditioning on mediators); GBM nuisances + linear final stage for smooth heterogeneous effects with closed-form CIs; Baron & Kenny mediator analysis showed ~76% of device effect flowed through sessions — marketing now nudges device + sessions together.
Validation: refutation tests (random common cause, placebo treatment, subset stability) all passed.

## Syqe Medical — Audio Classification for Embedded Deployment (2019)

15-class sound classification for a medical inhaler (Israel), 4,500 WAV files, deployed on a microcontroller via TFLite quantization. MFCC/spectral features (193 per clip) beat raw waveforms; a feed-forward network beat CNN on this dataset size (F1 0.86 vs 0.60). 97% training accuracy, 86% test F1.

## French Institute of Gynaecology — Clinical Outcome Prediction (2018-2019)

IUI fertility outcome prediction, 1,633 patients, 84 variables, 8.5% positive class. Evaluation switched entirely to precision/recall/F1 with repeated stratified K-fold; three-strategy feature selection (mutual information, backward elimination, embedded tree importances) plus RFECV over 130,000 CV tests. Deployed as clinical decision support.

## Quidnet Energy — Data Pipeline Automation (USA)

Automated multi-format ingestion (CSV/DTF/TXT) with auto-detection into aligned time series; rule-based injection/flowback event detection; smart downsampling (~90% size reduction on quiet periods, full resolution near events). Eliminated a daily manual bottleneck for the analytics team.

## Other Public GitHub Projects (github.com/gtraskas)

- **guardrail-api** — AI hallucination guardrail audit suite (portfolio project).
- **drug-discovery** — Drug discovery ML: SMILES, ADMET modeling, GNNs, AlphaFold, federated learning.
- **llm-portfolio** — Practical LLM projects: competitive intelligence analysis, multi-agent systems, RAG applications, autonomous AI solutions (Ollama, OpenAI).
- **knowledge-rag** — Domain-specific RAG knowledge base with conversational interface and source citations.
- **causal-trial-conversion-xdot** — Causal inference notebooks for trial conversion.
- **fake-news-detector** — Web app backed by a deployed SageMaker model.
- **post-race-analyzer** — Cycling race analysis: CdA optimization, weather and power models, race-plan simulation.
- **swim-analysis**, **power-curve-modeling** — sports-science analytics.
- **spamIt**, **titanic_prediction**, **breast_cancer_prediction**, **deep-learning-ai** — earlier ML fundamentals work.
