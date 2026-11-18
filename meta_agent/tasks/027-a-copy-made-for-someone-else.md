# 027 — A copy of this repository made for someone else

**Status:** open. Opened by `design-macbook-20261117-3` on 2026-11-18 on the person's words (`../../docs/ideas/20261118.md`, "A copy made for someone else seats meta by default": "배포를 할 때에는 메타 seat으로 자동지정되게 하면 될듯?", "반영해둬"). Nobody holds it.

**Seat:** the design role's. The tool that makes a copy, its tests and the rules it carries are in the design role's paths.

**Goal:** someone other than this lab can take a copy, open a session in it, and build agents in it from their first request. The session seats as meta with no question about roles, and the computer's tag is the only thing the copy's person is asked before the first seat.

**What landed with the person's words (2026-11-18):**
- `contracts/seats.json` `default_role: meta`. `python bootstrap.py seat` with no role takes it, and the standing rule of self-registration reads "or the default role when none is named" (root `CLAUDE.md`, `begin-session`).
- `python bootstrap.py machine <tag> "<which computer>" --write` records the tag the copy's person gives its computer, in `contracts/seats.json` and in the clone's git configuration. The person commits it alone before the first seat. A committer who is not a seat is reported, not refused.
- Tests: `../../contracts/tests/test_seat_defaults.py`, watched failing before the change.

**What is open (the design part):**
- A command that makes a copy for distribution. It writes a seat table with the roles, the default role and the rules, and no seats. It sets the copy's check 6 boundaries (`enforced_from`, `self_registration_from`) to the copy's first commit, so this lab's history is not judged against a table that no longer names its seats.
- What the copy carries. Recommended: the agent, the contracts, the skills and the templates; and not this lab's profile, requests, builds, cases, failure lines, notes, task claims or `docs/ideas/`, which are this lab's records.

**Waits for the person:**
- whether a distributed copy keeps this repository's git history or starts from one commit;
- what of this lab's records it carries (above, recommended);
- where it is published, if anywhere. A push is a publication, and publication scope is never inferred (MP11).

**Done when (read off a run):** a copy is made by the command into a folder outside this repository. In it, with a tag given, a fresh session seats as meta with no role named, the gate prints `VERDICT PASS`, and a request in a person's words reaches a build. The run is a test (`test-outside-the-repository`) and is removed after it is read.

**Must not:** publish a copy; infer what this lab's records may leave the lab; give a computer a tag the person did not give.
