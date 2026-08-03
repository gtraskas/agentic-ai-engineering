# AskGeorge roadmap

Planned improvements, in build order. Each phase is developed on its own
branch, verified locally against the checklist, and merged via a pull
request; merging to `master` auto-deploys to Modal.

## Phase 1 — First impression

Everything a visitor experiences in the first fifteen seconds after
clicking the link.

1. **Eliminate the cold start.** The app scales to zero, so the first
   visitor waits ~15 s while the container boots and the RAG index builds.
   Two measures: enable Modal memory snapshots (snapshot the imported,
   index-built process for fast cold boots) and set `min_containers=1` so
   one warm container is always ready (~$10/month at current Modal rates,
   inside the Starter plan's $30/month free credits).
   *Done when:* a cold hit renders in under ~3 s, a warm hit in under 1 s.
2. **Mobile pass.** Verify and fix 375 px and 768 px widths: the top bar
   (wordmark, name field, CV pills, links, theme toggle) needs a collapse
   strategy for small screens; the question-pill columns must stack; the
   hero must scale; the anchored tour cards must position correctly.
   *Done when:* no horizontal scroll and every control is usable at 375 px.
3. **Rich link previews.** OpenGraph and Twitter-card meta tags (title,
   description, portrait) plus a publicly served preview image, so the
   URL unfurls as a proper card in LinkedIn, WhatsApp, and Slack.
   *Done when:* a link-preview debugger shows photo, title, description.

## Phase 2 — Report portability and language

1. **Job-fit report export.** "Copy report" and "Download (.md)" actions
   under the generated report, so a recruiter can move the analysis into
   an ATS or an email without retyping.
2. **Answer in the visitor's language.** A prompt rule so questions asked
   in another language are answered in that language.

## Phase 3 — Follow-up suggestions

After each live answer, show two or three contextual follow-up questions
as clickable chips. Implementation: the model appends suggestions in a
machine-parseable tail of the same response (no second LLM call); the tail
is stripped from the visible answer and rendered as chips. Parsing is
fail-open — if the tail is absent or malformed, no chips are shown.
Chips are cleared together with the chat.

## Considered and rejected

- **Custom domain** — Modal gates custom domains behind the Team plan
  ($250/month), which is not justified; free reverse-proxy workarounds add
  moving parts for cosmetic gain. The `.modal.run` URL stays.
- **Daily analytics digest** — the existing notifications (contact
  requests, unknown questions, job-fit runs) already cover the signal.
- **"Ping the human" button** — redundant with the contact flow and the
  booking calendar.
