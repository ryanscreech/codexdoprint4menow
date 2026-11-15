# Operation: audit

Purpose: assess **all accessible project-related sessions** for missed efficiencies and underused findings, with transparent coverage.

## Procedure
1. Confirm project root and permitted transcript roots. Discover `CODEX_HOME` or default user `.codex/sessions/`, optionally `.codex/archived_sessions/`, and project-generated handovers. On Windows, inspect PowerShell `$env:CODEX_HOME` and `$HOME\.codex\sessions`. Do not assume a server, macOS or remote host history is accessible.
2. Build a **coverage manifest** before judging completeness. Enumerate JSONL and archived formats supported by environment; capture session ID, timestamp, cwd, topic/artifacts, evidence of project association, and inspection depth. Deduplicate approval/review forks and repeated session copies by ID/content. Never equate broad keyword matches with confirmed project membership.
3. Prefer metadata and compact handovers to classify. Inspect targeted events in *all confirmed related sessions*; list ambiguous/excluded sessions with reasons. For huge files work in bounded chunks.
4. Trace a timeline of tasks and artifacts: repeated datasheet parsing, rebuilt geometry, repeated environment setup, repeated failures, forgotten verification, deprecated methods, uncaptured user measurements, broken handovers, unsafe overwrite, untested fit assumptions and duplicated tooling.
5. Compare what each session discovered against the *next sessions'* actions. Record missed opportunities **with evidence**: was a prior verified STEP available? did later work redundantly reconstruct it? were previous failures repeated? were independent checks run? Were lessons proposed but never adopted?
6. Produce a prioritised audit table: finding ID, sessions, observation, cost mechanism, confidence, evidence location, suggested correction, effort, severity, and verification plan. Avoid imaginary time/token savings; split total/cached/uncached and per-session metrics.
7. Compare `cad-knowledge/` to transcript findings. Identify stale decisions, unbounded unknowns, missing hashes, absent next-action handovers and conflicts. Create proposed KB patches; do not auto-apply or change the global Skill without explicit authorisation.
8. Write `cad-knowledge/audits/AUDIT-YYYY-MM-DD.md` only with write permission. Include **coverage** (total discovered, confirmed, ambiguous, inspected, excluded, inaccessible), next-step plan, and outstanding hosts/archives.
9. State whether result is a **complete accessible-root audit** or **partial audit**. Never say "all project sessions" if only one host was checked.

## Suggested report headings
Scope and sources; coverage manifest; session-to-session timeline; repeat work; verification quality; knowledge gaps; efficiency opportunities; recommended process edits; rejected claims; measurement plan; unresolved access.
