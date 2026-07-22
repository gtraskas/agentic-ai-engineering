# AskGeorge

An AI representative for Georgios Traskas. It answers questions from recruiters and hiring managers in first person, with streaming replies, grounded strictly in George's professional background. Unknown questions, contact requests, and call bookings are emailed straight to George via Gmail SMTP — nothing is stored on the server's ephemeral disk.

## Architecture

```
askgeorge/
├── app.py                  # entry point: build_demo() + launch
├── deploy_modal.py         # Modal deployment (CPU, scales to zero)
├── core/
│   ├── config.py           # paths, models, env accessors
│   ├── profile.py          # background corpus loading
│   ├── knowledge.py        # in-memory Qdrant RAG (FastEmbed, local embeddings)
│   ├── prompts.py          # system prompt + per-question context injection
│   ├── tools.py            # tool schemas + shared dispatcher
│   ├── notifier.py         # Gmail SMTP notifications
│   ├── agent_scratch.py    # hand-rolled streaming tool-calling loop
│   └── agent_sdk.py        # OpenAI Agents SDK backend
├── ui/
│   ├── theme.py            # Aegean Minimal theme, CSS, layout
│   └── assets/             # photo.jpg, cv.pdf (optional)
└── me/                     # knowledge base (markdown)
```

- **LLM:** any model via [OpenRouter](https://openrouter.ai) — default `google/gemini-3.1-flash-lite` with reasoning effort capped at `low` for fast first tokens; switch anytime with `OPENROUTER_MODEL` / `ASKGEORGE_REASONING`
- **Two switchable agent backends:** a from-scratch tool-calling loop and the OpenAI Agents SDK (`AGENT_BACKEND=scratch|sdk`)
- **Input guardrail (SDK backend):** a parallel judge LLM with a Pydantic verdict blocks off-topic, dangerous, and prompt-injection messages before they reach the main agent (`ASKGEORGE_GUARDRAIL=0` to disable)
- **Rate limiting:** in-memory sliding windows — 15 messages/hour per visitor, 100/day globally — with polite first-person refusals
- **RAG:** documents chunked and embedded locally with FastEmbed, retrieved per question from `QdrantClient(":memory:")`; the summary stays pinned in the prompt
- **UI:** Gradio Blocks with a custom Aegean Minimal theme; drop your photo at `ui/assets/photo.jpg` and resumes at `ui/assets/cv_ai_ml_engineer.pdf` / `ui/assets/cv_data_scientist.pdf` to enable the header portrait and per-role Download CV buttons

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

The app is served at `https://<modal-username>--askgeorge-web.modal.run`.

### CI/CD

Every push runs lint + smoke tests via GitHub Actions; pushes to `master` auto-deploy to Modal when the `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` repository secrets are set (values live in `~/.modal.toml`).

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | yes | OpenRouter API key (openrouter.ai/keys) |
| `OPENROUTER_MODEL` | no | Override the chat model (default `google/gemini-3.1-flash-lite`) |
| `ASKGEORGE_REASONING` | no | Reasoning effort for thinking models (default `low`; e.g. `medium`, `high`) |
| `AGENT_BACKEND` | no | `sdk` (default, OpenAI Agents SDK) or `scratch` (from-scratch loop) |
| `ASKGEORGE_RAG` | no | Set `0` to disable RAG and pass the full corpus in context |
| `ASKGEORGE_GUARDRAIL` | no | Set `0` to disable the input guardrail (on by default) |
| `ASKGEORGE_TEMPERATURE` | no | Sampling temperature (default `0.2`) |
| `GMAIL_ADDRESS` | no | Gmail address that sends and receives notifications |
| `GMAIL_APP_PASSWORD` | no | Gmail App Password (Google Account → Security → 2-Step Verification → App passwords) |
| `CALENDAR_BOOKING_URL` | no | Google Calendar booking-page link; enables the embedded booking calendar |

Without Gmail credentials the app still works — notifications go to the application log instead.
