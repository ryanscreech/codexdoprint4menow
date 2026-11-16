# Install and update

This page describes the Codex integration. For another host, read [Using this toolkit with other agents](OTHER-AGENTS.md) first; the PowerShell installer uses the Codex paths and does not configure other clients.

## Windows (PowerShell)

Requirements: Git and a Codex client with local skill support, installed separately; PowerShell 5.1+. Python 3.9+ is optional for the session indexer and required for the test suite.

```powershell
git clone https://github.com/ryanscreech/codexdoprint4menow.git
cd codexdoprint4menow
Get-Content .\scripts\install.ps1
.\scripts\install.ps1 -WhatIf
.\scripts\install.ps1
```

The default installs the whole skill under `$HOME\.agents\skills\cad-continuity`. Identical installs are a no-op. Different existing content is refused unless `-Force` is supplied after review. A preview with `-WhatIf` writes nothing, including when differences exist.

Options:

- `-LegacyPrompts`: also installs the optional, deprecated slash wrappers under `$env:CODEX_HOME\prompts`, or `$HOME\.codex\prompts` if unset. They remain user-level even with `-ProjectLocal`.
- `-ProjectPath 'C:\CAD\MyProject'`: initialises `cad-knowledge` only if absent, while installing the user-level skill by default. The project must already exist. Existing project knowledge is preserved in full.
- `-ProjectLocal -ProjectPath 'C:\CAD\MyProject'`: installs the skill at `<project>/.agents/skills/cad-continuity` instead of user-level. Avoid installing the same skill at both scopes unless that duplication is intentional.
- `-Force`: replaces changed toolkit files after backing up the existing target. It never replaces an existing knowledge base.
- `-UserRoot <path>`: selects an alternative user directory for portable installation/testing; defaults to `$HOME`. An explicit `CODEX_HOME` still controls prompt placement.

The installer validates the complete plan before writes, stages and checks each copy before replacing its destination, and restores that destination if activation fails. It does not roll back earlier successful targets if a later target fails; inspect the reported paths and rerun after correcting the error. It rejects linked installation paths rather than following symlinks/junctions. Do not run simultaneous installers against the same targets.

Backups are at `<user-root>/.cad-continuity-backups/<unique-id>/previous`, or `<project>/.cad-continuity-backups/...` for a project-local installation. Each backup's original target is printed. These directories are outside skill discovery; keep project backups out of version control. Older installer versions created `cad-continuity.backup.*` inside `.agents/skills`; inspect and move those outside all skill discovery roots to avoid duplicate skills. Never discard customisations without review.

Merge the AGENTS example manually. Verify discovery in Codex; restart if the new skill is not visible. Test `$cad-continuity ingest <session>` and `$cad-continuity audit <project>` with explicitly read-only requests and permitted synthetic or known sessions. A successful file copy alone does not establish client discovery or useful agent behaviour.

If a client still exposes custom prompts, additionally verify `/prompts:ingest` and `/prompts:audit`. Restart that client after prompt changes. The source wrappers use `$$` to emit a literal skill-invocation dollar sign after prompt expansion.

## macOS/Linux

With PowerShell 7 available, use the same installer and options:

```bash
pwsh -NoProfile -File ./scripts/install.ps1 -WhatIf
pwsh -NoProfile -File ./scripts/install.ps1
```

Otherwise, this Bash fresh-install example refuses existing destinations, avoiding nested copies and accidental overwrites:

```bash
(
  set -eu
  destination="$HOME/.agents/skills/cad-continuity"
  if [ -e "$destination" ] || [ -L "$destination" ]; then
    echo "Destination exists; compare and back up outside .agents/skills before replacing." >&2
    exit 1
  fi
  mkdir -p "$HOME/.agents/skills"
  cp -R skills/cad-continuity "$destination"
)
```

For manual updates, compare the old and new skill, move the old directory to a unique backup outside every `.agents/skills` root, then copy the complete replacement to the now-absent destination. Preserve the backup if copying fails. For optional legacy prompts, inspect each existing file in `${CODEX_HOME:-$HOME/.codex}/prompts/` and back it up before copying its replacement. Do not blindly run `cp` over customised prompts.

## Project setup

Copy `templates/project-knowledge/` to `<project>/cad-knowledge/` only if missing. Merge guidance from `templates/AGENTS.project.example.md` with existing project `AGENTS.md`; do not replace existing rules. For a partially initialised knowledge base, review and copy only missing templates individually.

## Updates and uninstall

Check `git status --short`, preserve local edits, then run `git pull --ff-only` in the toolkit checkout. Review the changes and run the tests before installation. On PowerShell, preview with `-WhatIf` and use `-Force` for reviewed changes. Project knowledge is separate from the toolkit and remains intact.

To uninstall, remove only the installed skill folder and optional prompts after checking they belong to this toolkit. Restore any prior custom files from the printed backup locations if needed. Keep `cad-knowledge/` intact. Review project AGENTS references separately.

## Verification and compatibility

```bash
python3 -m unittest discover -s tests -v
```

On Windows use `py -3 -m unittest discover -s tests -v`. Tests use temporary directories and synthetic transcripts. PowerShell tests run when `pwsh` or `powershell` is available; otherwise they are explicitly skipped. To select a specific executable, set `CAD_TEST_POWERSHELL`. CI is configured for Linux, macOS, PowerShell 7 and Windows PowerShell 5.1; a workflow configuration is not evidence that those remote runs have passed.

Official compatibility references: [local skill discovery](https://learn.chatgpt.com/docs/build-skills), [deprecated custom prompts and argument expansion](https://learn.chatgpt.com/docs/custom-prompts), [AGENTS.md scope](https://learn.chatgpt.com/docs/agent-configuration/agents-md). Client versions can differ. These slash prompts are not built-in `/ingest` and `/audit`. No operation automatically gains access to sessions on another machine. Session schemas may vary by version; report unsupported coverage.
