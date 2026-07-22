# Engineering Practices — How George Builds Production AI

George's working methods, in his own words. Refined across MolekitChen, Wine-VFM, AskGeorge, consulting engagements, and four years of production work at Predictive Fitness.

## Preventing hallucinations

I treat hallucination as an engineering problem, not a model problem. Layers, not hope: retrieval quality first (get the right documents into context), deterministic lookups for exact numbers (never let the model invent a figure a table can provide), structured output contracts validated with Pydantic and retried on failure, citation cross-validation (every cited source must exist in the database or the answer is rejected), and low temperature for factual work.

## Retrieval craft

- **Hybrid search:** pure vector search finds meaning but misses exact terms; BM25 finds exact terms but misses meaning. I combine both with Reciprocal Rank Fusion, which merges ranked lists using positions only — no fragile score normalisation between different scoring scales. BM25 improves on TF-IDF with term-frequency saturation and document-length normalisation, which is why it handles chemical names and exact codes so well.
- **Chunking:** chunks sized to hold one coherent idea, split at sentence or heading boundaries, with overlap so nothing is lost at the seams. In MolekitChen: 512 tokens with 50-token overlap. In AskGeorge: heading-aware chunks that carry their section path.
- **Reranking and lost-in-the-middle:** models attend to the start and end of context and under-weight the middle, so I retrieve more candidates than needed, rerank, and pass only the best few — best material near the top.
- **Indexing:** HNSW gives approximate nearest-neighbour search in logarithmic time by navigating a layered graph — the "approximate" rarely matters when retrieving a handful of chunks, and the latency win is enormous versus brute-force comparison.

## Structured outputs

Every production LLM reply is forced into a typed schema (Pydantic). Malformed output fails validation and triggers a bounded repair loop — re-prompt with the error up to a few times, then a safe fallback. Silent unparseable output is how production AI systems rot. Field order matters: reasoning fields before the verdict, because the model fills the schema in order and thinking first improves the answer.

## Agents — when and how

- **Agent vs pipeline:** if the flow is predictable (retrieve then generate), a plain pipeline wins — agent overhead adds latency, cost, and non-determinism for nothing. An agent earns its place when the number and order of steps genuinely depends on intermediate results.
- **Framework rule of thumb:** predictable linear pipeline → LangChain; stateful, cyclical, conditional workflows → LangGraph; fully autonomous open-ended tasks → CrewAI or an SDK-based planner. On a team, use the team's stack — having built the layer underneath means I can debug the framework when it misbehaves.
- **Safety rails:** hard max-iteration limits, execution timeouts, and human-in-the-loop checkpoints before any irreversible action (database writes, external calls, sends). Runaway loops are a cost bug and a trust bug.
- **Agent memory:** in-context (the prompt window), external (database or vector store), episodic (logs of past runs), semantic (an embedded knowledge base). Memory is fundamentally just storing history somewhere and replaying it — the engineering is in choosing where it lives and what survives restarts.
- **Testing non-determinism:** golden test suites scored by semantic similarity (not string equality), LLM-as-a-judge for qualitative checks, full trace logging of every decision and tool call so incidents are reproducible, and bounded execution to shrink the surface of surprise.
- **Observability:** every agent interaction logs inputs, tool calls, outputs, token counts, latency, and errors. Token cost per task is a first-class metric — an agent that loops too much shows up as a cost spike before users notice. Agents fail in ways uptime monitoring never sees: wrong tool path with a right-looking answer, silent behavior change after a provider model update.
- **Tool design:** treat tool names and descriptions like API design — unambiguous, disjoint, with explicit "use when / don't use when" guidance. Tool selection degrades silently as toolkits grow; a golden query set with the known-correct tool per query, tested across strong and weak models, gates every addition.

## Prompt engineering as software engineering

Prompts live in a versioned registry committed to git, each version pinned to an exact model checkpoint with its evaluation scores. Changes create new versions, never in-place edits. A golden dataset of real questions gates deployment: if faithfulness, relevance, or precision drops, the new prompt or model does not ship. Model aliases like "latest" are never used in production — pin exact versions, upgrade through staging with side-by-side comparison. Prompt structure: clear role, user input wrapped in explicit tags so data is never mistaken for instructions, a few examples of perfect output, and a reasoning-before-answer instruction.

## Cost control

Cheapest tool that is accurate enough, at every step: regex and local libraries for input checks, small models for classification, big models only where they earn it. Two-tier caching: exact hash matches, then semantic near-duplicates above a high similarity threshold. Hard token budgets on prompt assembly with intelligent trimming (drop the weakest context first, keep a grounding floor). Most token waste is over-inclusive context — sending the model history or documents it does not need. Per-request cost tracking with alerts on drift.

## Context window management

Count tokens before assembling, not after failing. Reserve a fixed overhead for instructions and schema, give the rest to retrieved context, trim block-by-block when over budget. For long conversations, rolling summarisation: compress older turns into a paragraph rather than dropping them. Silent truncation is worse than an error — it produces confident answers with missing context.

## Security and privacy

- **Prompt injection:** defence in layers — input pattern screening, strict separation of system and user roles, and output validation so a hijacked reply fails the schema. In agentic systems the stakes are higher because agents hold tools; each agent gets only the tools its job needs.
- **Input guardrails:** cheap deterministic checks run before any expensive AI work — language allowlists, gibberish detection by character distribution, scope classification. Rejecting junk early saves tokens and reduces attack surface.
- **User data:** data minimisation (send the model only what the task needs), PII masking before anything crosses the network (placeholder substitution, mapped back locally), verified API terms per provider, and Row-Level Security so the database itself scopes what any session can see.
- **Content licensing:** deny-by-default ingestion — nothing enters a corpus without an explicitly verified open license, and every stored row carries its license tag so a compliance audit is one query.
- **Data lineage:** every AI-generated answer logs the prompt version, the exact model checkpoint, and the IDs of the context chunks used. When someone flags a bad answer, the failure localises to source data, retrieval, prompt, or model in minutes.

## Production reliability

- **Rate limits:** exponential backoff with jitter on retries — jitter prevents the thundering-herd effect where all clients retry at the same instant. Batch and pace bulk workloads to stay under provider quotas.
- **Provider outages:** a fallback chain of LLM providers with priority order; a single-provider dependency is an outage waiting to happen. Circuit breakers stop a dead dependency from being hammered.
- **Streaming:** stream tokens to the user (Server-Sent Events or framework streaming) — perceived latency matters more than actual latency. For very long operations, an async job pattern: return a job ID immediately, let the client poll.
- **Silent failures:** the most dangerous class. Defences: schema validation at ingestion that fails loudly, output distribution checks that flag anomalies even when accuracy metrics look normal, end-to-end golden smoke tests in CI/CD, and periodic human spot-checks. A real case: a device firmware update silently changed a sensor's units — the pipeline kept running and predictions kept flowing; output distribution monitoring caught the shifted histogram before users saw wrong results.

## MLOps: drift, retraining, rollout

- **Drift monitoring:** compare incoming data against the training baseline (Population Stability Index, KS tests) and alert on significant shift. Covariate drift (inputs change) and concept drift (the input-output relationship changes) need different responses. Always check first whether the data changed or the pipeline broke — they look identical from the outside.
- **Retraining:** trigger-based, never calendar-based — drift or metric degradation past defined thresholds. Retraining costs compute, attention, and risk; it must earn its trigger.
- **Rollout:** shadow mode first (real traffic, logged predictions, no user impact), then champion-challenger on a small traffic slice with automatic rollback on regression. Where ground truth lags by weeks, proxy metrics give fast feedback in the meantime.
- **Rollback:** pinned version identifiers for every model and prompt; promoting the previous version is one command and takes minutes.

## Deployment methodology (prototype to production)

1. Evaluate before deploying — golden dataset, judge scoring, hard thresholds.
2. Containerise with multi-stage Docker builds: lean images, non-root user, health checks, configuration only via environment variables.
3. CI/CD or nothing: every push builds, tests (including the golden smoke test), and deploys only on green. Never deploy by hand from a terminal — every deployment is a traceable, revertible commit.
4. Staged rollout: shadow, then a small slice, then full traffic after stable metrics.
5. Monitor from day one: errors and latency (Sentry), dashboards and drift (Grafana), infrastructure health (CloudWatch).
6. Keep rollback boring: pinned versions, one command, under five minutes.

## Python craft

- **Concurrency:** async/await for I/O-bound work — one event loop interleaves hundreds of waiting calls (LLM APIs, databases, HTTP); the cardinal sin is blocking the loop with synchronous work. Multiprocessing for CPU-bound work (the GIL prevents true parallel threads); threading only for simple I/O cases. `asyncio.gather` for concurrent independent calls.
- **FastAPI structure:** routers per domain, dependency injection for shared resources (database pools, auth, quotas — swap-able in tests), middleware for cross-cutting concerns, background tasks for post-response work. Stateless services so any instance can serve any request — session state lives in Redis or the database, never in the process.
- **Error handling:** specific exception types, never bare excepts; retries with `tenacity` (exponential backoff + jitter); log with context, fail loudly.
- **Pythonic by default:** generators for datasets that should never fully sit in memory, context managers for anything that must be cleaned up, comprehensions over loops, type hints everywhere — they are executable documentation and an early bug net.
- **Pandas at scale:** vectorised operations always (a Python loop over a million rows is a design smell), chunked reading for large files, or push the heavy aggregation to the database/Athena and pull back only results. Time-series work leans on resample/rolling with time-aware features.

## Cloud and infrastructure

Four years of production AWS: Lambda for event-driven ingestion triggers, ECS Fargate for containerised services that scale, S3 for raw and processed data, Athena for cheap ad-hoc SQL directly over S3, CloudWatch for infrastructure health. Infrastructure as code is the daily workflow (SST — same provider engine as Terraform): resources defined in code, deployed through pipelines, reviewable like any other change. GraphQL on the consumption side when different pipelines need different slices of the same entities — query exactly what each model needs, flatten the nested response immediately, and work in flat DataFrames after.

## Classic ML discipline

- **Leakage is the silent killer:** resampling (like SMOTE) happens inside each cross-validation fold only, never before splitting; chronological splits with a gap for time series; a user's data never straddles train and test.
- **Imbalanced data:** accuracy is meaningless at severe imbalance — a do-nothing model scores 90%+. Evaluate with precision, recall, macro-F1, and precision-recall curves; use stratified folds to keep class ratios stable; pick the operating threshold from the actual cost of each error type (in clinical work, a missed positive usually costs more than a false alarm).
- **Feature selection by consensus:** when filter methods, embedded importances, and recursive elimination all agree on the same features, the signal is real; when only one method likes a feature, be suspicious.
- **Calibration:** raw classifier scores are not probabilities; Platt calibration (or isotonic) makes "70%" mean 70%, which matters the moment a business decision consumes the number.
- **Small data:** prefer compact engineered features (e.g. MFCCs for audio instead of raw waveforms), regularise hard (dropout, early stopping), cross-validate everything, and don't default to the fashionable architecture — on one embedded audio project a feed-forward network on engineered features clearly beat a CNN that lacked the data to shine.

## Causal inference vs predictive ML

Prediction answers "what will happen"; causal inference answers "what happens if we act." Using a predictive model to choose interventions systematically targets people who would have converted anyway. When the question is which lever to pull, I build the causal graph first (confounders made explicit, mediators never conditioned on), estimate with Double Machine Learning (flexible models absorb the confounding, a simple final stage estimates the effect), validate with refutation tests (random common cause, placebo treatment, subset stability), and state the limits honestly: unmeasured confounding, overlap violations, and immature data are flagged, and the top levers get confirmed with A/B tests before anyone scales a campaign.

## Edge and embedded ML

For hardware-constrained deployment: optimise the architecture first (smaller layers, separable convolutions), then post-training quantization to 8-bit — roughly 4x smaller and much faster on integer hardware, typically a small accuracy cost. Calibrate quantization with a representative dataset, and validate on the physical device, never only the simulator — fixed-point arithmetic hides surprises that simulation misses.

## Working with stakeholders

Outcomes and levers, not metrics: "completing the tour raises conversion by X points — target users who haven't" lands; an AUC number does not. Separate dashboards for separate audiences (engineers get latency and errors; leadership gets conversion and noise reduction). A one-page design doc with five parts — problem in one sentence, solution in two registers (business paragraph first, technical paragraph second), tradeoffs considered, success metrics (one business, one technical), risks and open questions — reads correctly to a PM and a staff engineer at the same time. Validate requirements against actual usage before building: "real-time" often turns out to mean "by tomorrow morning", and a nightly batch that runs for a year unattended beats a streaming system nobody can maintain.
