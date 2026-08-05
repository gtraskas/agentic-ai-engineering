# AskGeorge

**Live:** https://gtraskas--askgeorge-web.modal.run

An AI representative for Georgios Traskas. It answers questions from recruiters and hiring managers in first person, with streaming replies, grounded strictly in George's professional background. Unknown questions, contact requests, and call bookings are emailed straight to George via Gmail SMTP — nothing is stored on the server's ephemeral disk.

## Architecture

```
askgeorge/
├── app.py                  # entry point: build_demo() + launch
├── deploy_modal.py         # Modal deployment (CPU, one warm container)
├── core/
│   ├── config.py           # paths, models, env accessors
│   ├── profile.py          # background corpus loading
│   ├── knowledge.py        # hybrid BM25+dense RAG in Qdrant (:memory:), FastEmbed
│   ├── language.py         # translates non-English questions for retrieval
│   ├── prompts.py          # system prompt + per-question context injection
│   ├── jobfit.py           # structured job-fit pipeline (parse/judge/synth/verify)
│   ├── guardrail.py        # parallel scope judge (Pydantic verdict, tripwire)
│   ├── ratelimit.py        # sliding-window rate limits (per-IP hourly, global daily)
│   ├── tools.py            # tool schemas + shared dispatcher
│   ├── notifier.py         # Gmail SMTP notifications
│   ├── agent_scratch.py    # hand-rolled streaming tool-calling loop
│   └── agent_sdk.py        # OpenAI Agents SDK backend (default)
├── ui/
│   ├── theme.py            # Terracotta theme, CSS, layout, rate-limit wrapper
│   └── assets/             # photo.jpg, CV PDFs
└── me/                     # knowledge base (markdown)

tests/
└── retrieval_eval.py       # golden-set retrieval eval, gates every CI run
```

- **LLM:** any model via [OpenRouter](https://openrouter.ai) — `google/gemini-3.1-flash-lite` (fast, consistent, ~$0.10/M input; pennies per day under the global rate cap) with reasoning effort capped at `low` for fast first tokens. Every call carries an OpenRouter server-side fallback chain to the best free model from the benchmark (`google/gemma-4-26b-a4b-it:free`), so a paid-model outage degrades to free instead of failing. Both model ids are constants in [`core/config.py`](core/config.py)
- **Two switchable agent backends:** a from-scratch tool-calling loop and the OpenAI Agents SDK (`AGENT_BACKEND=scratch|sdk`)
- **Input guardrail (SDK backend):** a parallel judge LLM with a Pydantic verdict blocks off-topic, dangerous, and prompt-injection messages before they reach the main agent
- **Rate limiting:** in-memory sliding windows — 15 messages/hour per visitor, 100/day globally — with polite first-person refusals
- **Browser-side persistence:** the conversation lives in the visitor's own browser (encrypted localStorage via gr.BrowserState) and is restored on page load; Clear chat wipes it
- **Prompt pills:** six suggested questions under the composer. Every one goes through the live RAG + LLM path, and the CI eval asserts each is either covered by the retrieval golden set or explicitly recorded as prompt-answered, so no pill ships unverified
- **Any language:** questions are answered in the language they were asked in. Because the corpus and the embedding model are English-only, a non-English question is translated to English for the retrieval step before it is searched, so the answer stays grounded instead of fluent-but-thin. Questions that are already English skip the call, so the common path costs nothing
- **Report download:** a finished job-fit report can be downloaded as Markdown. Each report is written to its own temp directory, so concurrent visitors can never be served each other's analysis
- **Job-fit analysis:** a dedicated tab where a recruiter pastes a job description; a structured pipeline (parse → per-requirement RAG judgment via `asyncio.gather` → deterministic band → synthesis → anti-flattery verifier) returns an honest, evidence-backed fit report and emails George each run. The description is treated as untrusted input
- **RAG:** hybrid dense + sparse (BM25) retrieval, embedded locally with FastEmbed and fused in `QdrantClient(":memory:")`; heading-aware chunking; the summary stays pinned in the prompt; a retrieval golden-set eval gates every CI run
- **UI:** Gradio Blocks with a custom Terracotta theme; the header portrait and the per-role Download CV buttons appear when `ui/assets/` holds `photo.jpg` and the two CV PDFs named in [`ui/theme.py`](ui/theme.py). The layout adapts down to 375 px wide phones
- **Link previews:** OpenGraph and Twitter-card meta tags plus a preview card at `/media/og_card.jpg`, so the shared URL unfurls with a portrait, title, and description in LinkedIn, WhatsApp, and Slack

## Design decisions

The reasoning behind the parts that are not obvious from the code.

- **In-memory Qdrant instead of a hosted vector database.** The corpus is a handful of
  Markdown files and static between deployments — an always-on database would cost
  money to sit idle. Rebuilding the index in RAM at container start takes seconds and
  leaves nothing to operate or secure.
- **One warm container instead of scale-to-zero.** The first visitor used to wait
  ~15 s for a container boot and index build. `min_containers=1` keeps one container
  always ready (~$10/month, inside Modal's free Starter credits), and
  `@modal.concurrent` lets it serve all realistic traffic, so every visit is warm.
  Memory snapshots were considered and skipped: with a warm container they would only
  speed the rare post-deploy boot, which is not worth restructuring the serving app.
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
- **Non-English questions are translated for search, not for the answer.** The corpus
  is English and `BAAI/bge-small-en-v1.5` is an English-only embedding model, so a Greek
  or German question embeds poorly and retrieval returns weak chunks the model then
  answers from fluently. Measured before the change, a Greek question about the alerting
  work and a German one about notice period both missed their expected chunks entirely.
  Translating the query first fixes both. A cheap function-word check skips the extra
  call for questions that are already English, which is nearly all of them.
- **No canned answers.** An earlier version served curated replies to the most common
  recruiter questions with no model call — free, instant, and a lie about the product.
  The questions most likely to be asked were exactly the ones that never reached the
  model, so the busiest path through a page whose whole claim is "this is how I answer"
  was a lookup table. Every message now goes to the model. The cost is real: those
  questions used to bypass the rate limiter and now consume the global daily budget.
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
| `AGENT_BACKEND` | no | `sdk` (default, OpenAI Agents SDK) or `scratch` (from-scratch loop) |
| `ASKGEORGE_RAG` | no | Set `0` to disable RAG and pass the full corpus in context |
| `GMAIL_ADDRESS` | no | Gmail address that sends and receives notifications |
| `GMAIL_APP_PASSWORD` | no | Gmail App Password (Google Account → Security → 2-Step Verification → App passwords) |
| `CALENDAR_BOOKING_URL` | no | Google Calendar booking-page link; enables the embedded booking calendar |

Without Gmail credentials the app still works — notifications go to the application log instead.
