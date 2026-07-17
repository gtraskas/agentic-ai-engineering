# AskGeorge

An AI representative for Georgios Traskas. It answers questions from recruiters and hiring managers in first person, grounded strictly in George's professional background (`me/` directory: LinkedIn export, summary, project portfolio). Unknown questions and contact requests trigger push notifications via Pushover (optional).

- **UI:** Gradio `ChatInterface`
- **LLM:** Google Gemini Flash via the OpenAI-compatible API (free tier)
- **Hosting:** Modal (CPU container, scales to zero)

## Run locally

```bash
uv sync
cp .env.example .env   # add your GOOGLE_API_KEY
uv run python askgeorge/app.py
```

## Deploy to Modal

```bash
uv run modal setup                                   # once
uv run modal secret create askgeorge-secret \
    GOOGLE_API_KEY=... PUSHOVER_TOKEN=... PUSHOVER_USER=...
uv run modal deploy askgeorge/deploy_modal.py
```

The app is served at `https://<modal-username>--askgeorge-web.modal.run`.

## Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `GOOGLE_API_KEY` | yes | Gemini API key (aistudio.google.com) |
| `PUSHOVER_TOKEN` | no | Pushover app token for notifications |
| `PUSHOVER_USER` | no | Pushover user key for notifications |
