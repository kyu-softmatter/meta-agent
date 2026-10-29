# Materials inbox

A link on one line is enough.

## What you do

Either of these, at any time — before, during or after setup:

- **A link.** Add one row to [`LINKS.md`](LINKS.md). Only the `url` column is required; `name`, `role` and `note` are optional and you may leave them blank. Leave `card` blank; the Meta-Agent fills it.
- **A file.** Put a PDF, a document or an archive into [`drop/`](drop/). You do not need to rename it.

Manuals, API or scripting documentation, papers, specification sheets, tutorial cases and repository links for any simulation engine or instrument the lab uses or plans to use are welcome. The first ones needed are the lab's rheometer (model, control software, API, data export format) and the rheology simulation engine the lab chooses (`../../../plan.md` 14-20, 14-21).

## What happens next

1. The Meta-Agent sees the new row or file, creates `inbox/materials/<YYYYMMDD>-<slug>/`, moves the file into it and writes `MATERIAL.json`. It writes the card id back into your row in `LINKS.md`.
2. It fills `kind`, `about` (name, role, methods) and `license_note` as **inferred**, each with evidence from the content. What it cannot infer stays **unknown** and becomes a question.
3. A URL is fetched once, read-only and anonymously, and `retrieved_at` and `content_hash` are recorded. A link behind a login or paywall is not fetched: the card is `held` with `permission_required` until you say how.
4. You are shown what was filled and the questions, once. When you confirm, the card is `registered`; the knowledge engine then distils it (`distilled`). Material that is a duplicate, out of scope or licence-blocked is `declined` with a reason.
5. If the material is about a new engine or instrument, only the discovery step of onboarding re-runs for that item, and a new revision of the lab profile and a registry update are **proposed** for you to confirm.

Design and build never wait for material. While something is missing, the tool's profile simply keeps an `unknown` claim that says what would resolve it.

## What is never done

- Your credentials or logged-in sessions are never used to fetch anything.
- A verbatim copy of a document is kept only when you set `may_quote: true` on its card or the licence plainly allows it; otherwise only the hash and the location are kept.
- Another agent never drops material here directly; anything arriving over the bridge comes to you first.

## The card

`MATERIAL.json` follows `../../../contracts/schemas/material.schema.json`. The only field you write is `location` (and `about.name` if you like). The states are `queued → registered → distilled | declined | held`. Check 17 of `../../../contracts/validate.py` enforces the rules above.

Intake runs from M2 (`../../../plan.md` 12). Until then a row you add waits here, and that is fine.
