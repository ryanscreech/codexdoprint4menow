# Install and update

## Windows (PowerShell)

Requirements: Git and Codex installed separately; PowerShell 5.1+.

```powershell
git clone https://github.com/ryanscreech/codexdoprint4menow.git
cd codexdoprint4menow
Get-Content .\scripts\install.ps1   # inspect before running
.\scripts\install.ps1 -WhatIf
.\scripts\install.ps1 -LegacyPrompts
```

Default installs the skill under `$HOME\.agents\skills\cad-continuity`. `-LegacyPrompts` additionally copies optional slash wrappers to `$CODEX_HOME\prompts` (or `$HOME\.codex\prompts`). Old files get timestamped backups. Add `-ProjectPath 'C:\CAD\MyProject'` to initialise a *missing* project knowledge base; it will not overwrite an existing one. Merge the AGENTS example by hand.

Restart Codex. Verify `$cad-continuity ingest <session>` and `$cad-continuity audit <project>` in read-only mode. If your client supports legacy prompts, additionally test `/prompts:ingest` and `/prompts:audit`.

## macOS/Linux

```bash
git clone https://github.com/ryanscreech/codexdoprint4menow.git
cd codexdoprint4menow
mkdir -p ~/.agents/skills
cp -R skills/cad-continuity ~/.agents/skills/
# optional, for legacy-client support:
mkdir -p "${CODEX_HOME:-$HOME/.codex}/prompts"
cp prompts/{ingest,audit}.md "${CODEX_HOME:-$HOME/.codex}/prompts/"
```

Inspect/backup existing installed directories before replacement.

## Project setup

Copy `templates/project-knowledge/` to `<project>/cad-knowledge/` only if missing. Merge guidance from `templates/AGENTS.project.example.md` with existing project `AGENTS.md`; do not replace existing rules.

## Updates and uninstall

Run `git pull --ff-only`, review changes, then repeat installation. Existing project knowledge stays separate and is never replaced by updates. To uninstall, remove only the installed skill folder and optional prompts after checking they belong to this toolkit. Keep `cad-knowledge/` intact.

## Limitations

The slash prompt paths are legacy, not built-in `/ingest` and `/audit`; on unsupported clients use `$cad-continuity`. No operation can read a session from an inaccessible machine automatically. Session log schemas may vary by Codex version.
