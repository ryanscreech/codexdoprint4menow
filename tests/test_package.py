"""Dependency-free structural validation."""
from pathlib import Path
root = Path(__file__).resolve().parent.parent
required = [
 "README.md","LICENSE","docs/INSTALL.md","docs/SECURITY.md","scripts/install.ps1",
 "prompts/ingest.md","prompts/audit.md","skills/cad-continuity/SKILL.md",
 "skills/cad-continuity/references/INGEST.md","skills/cad-continuity/references/AUDIT.md",
 "skills/cad-continuity/references/MODEL.md","templates/AGENTS.project.example.md",
 "templates/project-knowledge/INDEX.md","templates/project-knowledge/HANDOFF.md",
 "templates/project-knowledge/LESSONS.md","templates/project-knowledge/DECISIONS.md",
 "templates/project-knowledge/UNRESOLVED.md","templates/project-knowledge/SOURCES.md"
]
for p in required:
    assert (root/p).is_file(), f"Missing: {p}"
skill=(root/"skills/cad-continuity/SKILL.md").read_text(encoding="utf-8")
assert skill.startswith("---\n") and "name: cad-continuity" in skill
for c in ("ingest","audit"):
    cmd=(root/f"prompts/{c}.md").read_text(encoding="utf-8")
    assert "$ARGUMENTS" in cmd and "cad-continuity" in cmd
assert "Agent installation" in (root/"README.md").read_text(encoding="utf-8")
print(f"PASS {len(required)} required files + command assertions")
