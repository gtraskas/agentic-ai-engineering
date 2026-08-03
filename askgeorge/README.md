# AskGeorge

**Live:** https://gtraskas--askgeorge-web.modal.run

An AI representative for Georgios Traskas. It answers questions from recruiters and hiring managers in first person, with streaming replies, grounded strictly in George's professional background. Unknown questions, contact requests, and call bookings are emailed straight to George via Gmail SMTP — nothing is stored on the server's ephemeral disk.

## Architecture

```
askgeorge/
├── app.py                  # entry point: build_demo() + launch
├── deploy_modal.py         # Modal deployment (CPU, scales to zero)
├── core/
│   ├── config.py           # paths, models, env accessors
│   ├── profile.py          # background corpus loading
│   ├── instant.py          # instant FAQ answers (no LLM call)
│   ├── knowledge.py        # hybrid BM25+dense RAG in Qdrant (:memory:), FastEmbed
│   ├── prompts.py          # system prompt + per-question context injection
│   ├── jobfit.py           # structured job-fit pipeline (parse/judge/synth/verify)
│   ├── guardrail.py        # parallel scope judge (Pydantic verdict, tripwire)
│   ├── ratelimit.py        # sliding-window rate limits (per-IP hourly, global daily)
│   ├── tools.py            # tool schemas + shared dispatcher
│   ├── notifier.py         # Gmail SMTP notifications
│   ├── agent_scratch.py    # hand-rolled streaming tool-calling loop
│   └── agent_sdk.py        # OpenAI Agents SDK backend (default)
├── ui/
│   ├── theme.py            # Refined Aegean theme, CSS, layout, rate-limit wrapper
│   └── assets/             # photo.jpg, CV PDFs
└── me/                     # knowledge base (markdown)

tests/
├── retrieval_eval.py       # golden-set retrieval eval, gates every CI run
└── instant_eval.py         # instant-FAQ matcher eval, gates every CI run
```

- **LLM:** any model via [OpenRouter](https://openrouter.ai) — default `nvidia/nemotron-3-super-120b-a12b:free` (benchmarked best free tool-calling model: ~1.5–1.9s to first token, reliable tool calls, valid guardrail JSON) with reasoning effort capped at `low` for fast first tokens; switch anytime with `OPENROUTER_MODEL` / `ASKGEORGE_REASONING`
- **Two switchable agent backends:** a from-scratch tool-calling loop and the OpenAI Agents SDK (`AGENT_BACKEND=scratch|sdk`)
- **Input guardrail (SDK backend):** a parallel judge LLM with a Pydantic verdict blocks off-topic, dangerous, and prompt-injection messages before they reach the main agent (`ASKGEORGE_GUARDRAIL=0` to disable)
- **Rate limiting:** in-memory sliding windows — 15 messages/hour per visitor, 100/day globally — with polite first-person refusals
- **Instant FAQ answers:** the most common recruiter questions return a curated first-person reply immediately — no retrieval, no model call, no API cost — and don't consume the visitor's rate-limit budget. Matching is conservative (normalized exact + high-bar fuzzy), and a two-sided eval in CI guards against both misses and false positives
- **Question pills:** four curated pills under the chat input, with the full catalog in a "More questions" expander split into "Quick answers" (rendered straight from the instant-FAQ catalog, so UI and matcher can't drift apart) and "Ask the AI live" (questions from the retrieval golden set that demonstrate the RAG + LLM pipeline). One click submits the question
- **Job-fit analysis:** a dedicated tab where a recruiter pastes a job description; a structured pipeline (parse → per-requirement RAG judgment via `asyncio.gather` → deterministic band → synthesis → anti-flattery verifier) returns an honest, evidence-backed fit report and emails George each run. The description is treated as untrusted input
- **RAG:** hybrid dense + sparse (BM25) retrieval, embedded locally with FastEmbed and fused in `QdrantClient(":memory:")`; heading-aware chunking; the summary stays pinned in the prompt; a retrieval golden-set eval gates every CI run
- **UI:** Gradio Blocks with a custom Aegean Minimal theme; the header portrait and the per-role Download CV buttons appear when `ui/assets/` holds `photo.jpg` and the two CV PDFs named in [`ui/theme.py`](ui/theme.py)

## Design decisions

The reasoning behind the parts that are not obvious from the code.

- **In-memory Qdrant instead of a hosted vector database.** The corpus is a handful of
  Markdown files and static between deployments, and the app scales to zero — an
  always-on database would cost money to sit idle. Rebuilding the index in RAM at
  container start takes seconds and leaves nothing to operate or secure.
- **The job-fit score is computed in code, not by the model.** The pipeline parses the
  job description into typed requirements, judges each one against retrieved evidence
  concurrently, then derives the overall band deterministically in Python — so a
  must-have gap can never be rendered as a strong fit. A final anti-flattery pass
  regenerates the report if it overclaims.
- **A retrieval eval gates every deploy.** 23 recruiter-style questions each assert an
  expected fact appears in the retrieved context. Any corpus or chunking change that
  silently breaks recall fails the build instead of reaching visitors.
- **The guardrail is a parallel judge, not a preflight check.** The scope check runs
  concurrently with answer generation, so legitimate visitors pay no latency; the
  tripwire cancels generation only when the judge rejects. It reads the visitor's raw
  message from the run context rather than reconstructing it from the augmented prompt,
  which would let a visitor shrink the judged text and slip past.
- **Hybrid dense and sparse retrieval.** Dense embeddings catch meaning; a local BM25
  model catches exact terms like tool names and acronyms. Chunks carry their Markdown
  heading path, so retrieval matches on section context rather than body text alone.
- **Embeddings run locally.** FastEmbed inside the container means no API call and no
  per-query cost at question time; the model is baked into the image so cold starts
  skip the download.
- **Two agent backends on purpose.** The from-scratch streaming tool-calling loop shows
  what a framework abstracts — delta assembly, tool rounds, safety caps — and the
  Agents SDK version delivers the same behaviour in a tenth of the code. Build the
  baseline, then let the abstraction earn its place.
- **Instant answers are matched conservatively on purpose.** Only a normalized exact
  match or a near-identical fuzzy match (0.90 similarity) against curated trigger
  phrasings returns a canned reply; anything else goes to the full pipeline. A canned
  answer to a question it does not quite fit reads worse than a slower real one, so
  the CI eval asserts pass-throughs ("Are you open to relocating?") as strictly as
  matches.
- **Grounding instead of server-side memory.** The model answers only from retrieved
  background; conversation history is replayed from the browser each turn. The correct
  stateless pattern for serverless, and immune to container restarts.

## Run locally

```bash
uv sync
cp .env.example .env   # add your OPENROUTER_API_KEY (Gmail + booking URL optional)
uv run python -m askgeorge.app
```

## Deploy to Modal

```bash
uv run modal secret create askgeorge-secret \
    OPENROUTER_API_KEY=... GMAIL_ADDRESS=... GMAIL_APP_PASSWORD=... CALENDAR_BOOKING_URL=...
uv run modal deploy askgeorge/deploy_modal.py
```

The app is served at https://gtraskas--askgeorge-web.modal.run.

### CI/CD

Every push runs lint + smoke tests via GitHub Actions; pushes to `master` auto-deploy to Modal when the `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` repository secrets are set (values live in `~/.modal.toml`).

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | yes | OpenRouter API key (openrouter.ai/keys) |
| `OPENROUTER_MODEL` | no | Override the chat model (default `nvidia/nemotron-3-super-120b-a12b:free`) |
| `JOBFIT_MODEL` | no | Override the job-fit model (defaults to the chat model) |
| `ASKGEORGE_REASONING` | no | Reasoning effort for thinking models (default `low`; e.g. `medium`, `high`) |
| `AGENT_BACKEND` | no | `sdk` (default, OpenAI Agents SDK) or `scratch` (from-scratch loop) |
| `ASKGEORGE_RAG` | no | Set `0` to disable RAG and pass the full corpus in context |
| `ASKGEORGE_GUARDRAIL` | no | Set `0` to disable the input guardrail (on by default) |
| `ASKGEORGE_TEMPERATURE` | no | Sampling temperature (default `0.7`) |
| `GMAIL_ADDRESS` | no | Gmail address that sends and receives notifications |
| `GMAIL_APP_PASSWORD` | no | Gmail App Password (Google Account → Security → 2-Step Verification → App passwords) |
| `CALENDAR_BOOKING_URL` | no | Google Calendar booking-page link; enables the embedded booking calendar |

Without Gmail credentials the app still works — notifications go to the application log instead.
