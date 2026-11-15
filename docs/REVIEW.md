# Toolkit review

Reviewed baseline: `0d68d91` (2026-11-15). Scope: all tracked toolkit files, intended CAD/session-continuity workflow, installer behaviour and validation. No original private CAD project or transcripts are included in this repository.

## Assessment

The use case is sound: evidence-linked dimensions, reusable geometry, export verification and compact handovers can reduce repeated investigation across CAD sessions. The repository is an agent workflow package, not an automated CAD or printing system. Its effectiveness still depends on an agent following the procedure, accessible source material, appropriate CAD readers and physical testing where fit matters. No measured time or token improvement was established by the original package checks.

## Findings and changes

| Finding at baseline | Consequence | Applied change |
| --- | --- | --- |
| Installer replaced existing skills/prompts by default despite the README's preservation guidance | Custom instructions could be displaced without explicit update intent | Changed content requires `-Force`; identical content is a no-op; all planned conflicts and project paths are checked before writes |
| Skill backups lived inside `.agents/skills` | Old and new skills could both be discovered | Unique backups outside discovery roots; migration advice for older backups |
| Existing skill was moved before the new copy was prepared; backup names had one-second precision | Copy failure could leave no active skill; repeated updates could collide | Verified staging before replacement, unique backup IDs, tested per-target restoration after activation failure |
| `-ProjectPath` was checked only after installing user files; no project-local install option | A typo could leave a partial install; scope selection required manual copying | Early validation and explicit `-ProjectLocal` |
| macOS/Linux copy examples could merge/nest an existing skill or overwrite prompts | Updates could retain stale files or displace customisations | Fresh-install commands refuse existing targets; explicit replacement/update guidance |
| Audit instructed deduplication of approval/review forks by ID/content | Distinct corrections or appended events could be lost | Only exact copies deduplicated; forks and same-ID changed files retained |
| No executable session indexing support | Each agent had to invent its own scanning and coverage handling | Streaming standard-library indexer with hashes, line locations, bounded samples, exclusions and incomplete-input exit status |
| Token guidance did not distinguish cumulative snapshots from increments | Repeated totals could be added and cache subsets double-counted | Last-snapshot guidance, subset/inherited-counter caveats and regression tests |
| Export checks did not distinguish B-rep from mesh readers or 3MF placement transforms | A nominal box or the wrong reader could be mistaken for delivery validation | Format-specific checks, editable-source retention, independent expectations and explicit unsupported checks |
| Mandatory lesson counts and broad skill description | Pressure to invent findings or activate for unrelated audits | Up to five supported lessons, including zero; CAD-specific routing and respect for already authorised writes |
| Tests used top-level `assert` statements and checked only files/strings | `python -O` could remove assertions; unittest discovery reported no actual test cases for that file | Discoverable unittest cases plus behavioural installer/indexer regressions; cross-platform CI configuration |

## Verification record

- `CAD_TEST_POWERSHELL=/tmp/cad-review-powershell/pwsh PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`: **22 tests passed**, no skips, 21.873 seconds on Linux.
- `python3 -O tests/test_package.py`: package checks also pass with Python assertions disabled.
- Skill-creator `quick_validate.py skills/cad-continuity`: **Skill is valid**.
- `git diff --check`: passed.
- Synthetic CLI scan: 100,001 records / 25,300,090 input bytes produced a 949-byte metadata index in 0.612 seconds on this machine. Record counts and parsing status were checked; semantic audit status remained false. This repetitive fixture exercises bounded output and scanning, not real-project comprehension, privacy certification or token savings.

Local behavioural tests run with synthetic JSONL fixtures and temporary installation directories. The PowerShell runtime used for Linux validation is a temporary upstream PowerShell 7.7.0 distribution verified against its published SHA-256; the toolkit was not installed into the reviewer's live Codex configuration.

Tests cover preview with no writes, repeat installation, explicit replacement, backups outside discovery, invalid paths, prompt conflicts, project-local scope, preservation of knowledge, recovery after simulated activation failure, transcript damage, unsupported inputs, exact duplicates, distinct histories, Windows/POSIX path boundaries, token counters and content omission.

Native Windows PowerShell 5.1, macOS, actual Codex skill discovery, real modelling sessions and physical CAD/print acceptance remain unverified locally. CI includes the first two platforms but has not been run on GitHub as part of this local review. Package validation and synthetic tests do not establish modelling quality or savings.

## Sources checked

- [OpenAI skill discovery](https://learn.chatgpt.com/docs/build-skills): local scope and duplicate skill names.
- [OpenAI custom prompts](https://learn.chatgpt.com/docs/custom-prompts): deprecated interface, argument expansion and literal dollar escaping.
- [OpenAI AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md): project instruction scope.
- [CadQuery import/export](https://cadquery.readthedocs.io/en/latest/importexport.html): supported readers/writers, mesh formats and parametric source limitations.
- [3MF Core specification](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md): units, components and build placement.
