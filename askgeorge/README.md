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

## Roadmap

- [ ] **Custom design** — branded Gradio theme with custom CSS/JS: header card (name, links, open-to-work badge), avatar on assistant messages, dark-mode aware styling, footer with contact buttons.
- [ ] **In-memory Qdrant RAG** — ingest additional background documents, chunk and embed them locally with FastEmbed, retrieve top-k per question via `QdrantClient(":memory:")` while keeping the summary pinned in the prompt.
- [ ] **Agent framework migration** — port the from-scratch tool-calling loop to the OpenAI Agents SDK (OpenRouter-compatible), keeping the current implementation as a baseline for comparison.
- [ ] **More tools:**
  - `get_live_github_projects` — fetch current repos from the GitHub API so project answers never go stale
  - `analyze_job_fit` — recruiter pastes a job description, agent returns an honest fit assessment against the profile
  - `send_cv` — share a downloadable resume PDF
  - `schedule_intro_call` — offer a booking link and email George the context
  - `search_background` — expose RAG retrieval as a tool the agent invokes on demand
