# AskGeorge

An AI representative for Georgios Traskas. It answers questions from recruiters and hiring managers in first person, with streaming (token-by-token) replies, grounded strictly in George's professional background (`me/` directory: LinkedIn profile, summary, project portfolio). Unknown questions and contact requests are emailed straight to George via Gmail SMTP — nothing is stored on the server's ephemeral disk.

- **UI:** Gradio `ChatInterface` (streaming)
- **LLM:** any model via [OpenRouter](https://openrouter.ai) — default `google/gemini-3.5-flash`, switchable with one env var
- **Hosting:** Modal (CPU container, scales to zero)

## Run locally

```bash
uv sync
cp .env.example .env   # add your OPENROUTER_API_KEY (and Gmail credentials, optional)
uv run python askgeorge/app.py
```

## Deploy to Modal

```bash
uv run modal setup                                   # once
uv run modal secret create askgeorge-secret \
    OPENROUTER_API_KEY=... GMAIL_ADDRESS=... GMAIL_APP_PASSWORD=...
uv run modal deploy askgeorge/deploy_modal.py
```

The app is served at `https://<modal-username>--askgeorge-web.modal.run`.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | yes | OpenRouter API key (openrouter.ai/keys) |
| `OPENROUTER_MODEL` | no | Override the chat model (default `google/gemini-3.5-flash`) |
| `GMAIL_ADDRESS` | no | Gmail address that sends and receives lead notifications |
| `GMAIL_APP_PASSWORD` | no | Gmail App Password (Google Account → Security → 2-Step Verification → App passwords) |

Without Gmail credentials the app still works — notifications go to the application log instead.
