# Optional session indexer

Use `scripts/index_sessions.py` relative to the installed skill directory. Requires Python 3.9+ and no third-party packages. It reads only supplied files/directories, writes JSON to stdout, executes no transcript commands and performs no network requests.

From this repository on Linux/macOS:

```bash
python3 skills/cad-continuity/scripts/index_sessions.py /permitted/session.jsonl --project /CAD/MyProject
# Or index explicitly permitted roots, including archives if separately authorised:
python3 skills/cad-continuity/scripts/index_sessions.py /permitted/sessions /permitted/archived_sessions --project /CAD/MyProject
```

Windows PowerShell, with Python installed:

```powershell
py -3 "$HOME\.agents\skills\cad-continuity\scripts\index_sessions.py" 'C:\permitted\sessions' --project 'C:\CAD\MyProject'
```

Without Python, use bounded native JSONL reads and maintain the same evidence/coverage fields manually. Do not install a runtime merely to index a small nominated session if the available tools suffice.

## Interpretation

- One streaming pass records each JSONL's SHA-256, physical line count, session IDs, recorded cwd values, event counts and up to eight line locators per event category. Samples locate evidence; they are not an exhaustive list of tool calls or a semantic review. Inspect targeted ranges in the original file for conclusions.
- No message bodies, tool arguments or tool outputs are emitted. **Metadata still contains private paths and IDs.** Keep output local and inspect it before sharing. Saving the output is a write; honour the current task's write scope. Preserve a saved manifest as a snapshot rather than overwriting prior reports.
- Only `.jsonl` is supported. Unsupported files/archives, missing paths and discovered symlinks are listed as exclusions; directory links are not traversed. Unknown top-level schemas, malformed/truncated JSON, missing session identities and unreadable files are reported. Lines over 8 MiB are hashed but not parsed, and coverage is marked incomplete. Event and issue samples are bounded; counts are not truncated.
- Exit `0` means at least one file was indexed with no parse issues or exclusions. Exit `1` means incomplete input coverage; the JSON still contains the usable results. Argument errors exit `2`. **Exit 0 never means an audit is complete.** `semantic_audit_complete` is always false.
- `cwd_match` means a recorded cwd equals or lies under the project path. Matching is lexical, using Windows drive/UNC case rules for Windows paths and case-sensitive POSIX rules otherwise. Aliases, symlinks, relocated projects and worktrees need manual association. `needs_review` is not an exclusion. A transcript can cover more than one project.
- `exact_duplicate_of` marks only identical, successfully parsed file bytes. All entries remain visible. `same_id_different_content` requires review; never discard a newer suffix or a fork's unique events. Hashes/line references refer to the scanned snapshot; `changed_during_read` invalidates complete parsing status. Re-index active files after they settle.
- `last_reported_total_usage` preserves the last available valid cumulative snapshot and its line. It is not summed, not necessarily attributable solely to this file, and not a savings measurement. Forks/resumed logs can inherit counters. Missing fields stay absent; cached input and reasoning output can be subsets of other totals. Inspect resets/schema changes before doing arithmetic.

For large archives, use an existing manifest to select changed/new files and unresolved candidates; the helper itself does not maintain a cache. Store the selected roots and unreviewed candidates alongside any report. Do not describe an incremental subset as a complete audit of all sessions.
