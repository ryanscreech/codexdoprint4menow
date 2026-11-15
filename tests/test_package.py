"""Package integrity checks; run directly or with unittest discovery."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_required_resources(self):
        required = [
            'README.md', 'LICENSE', 'docs/INSTALL.md', 'docs/SECURITY.md', 'scripts/install.ps1',
            'prompts/ingest.md', 'prompts/audit.md', 'skills/cad-continuity/SKILL.md',
            'skills/cad-continuity/references/INGEST.md', 'skills/cad-continuity/references/AUDIT.md',
            'skills/cad-continuity/references/MODEL.md', 'skills/cad-continuity/references/INDEXER.md',
            'skills/cad-continuity/scripts/index_sessions.py', 'templates/AGENTS.project.example.md',
            *[f'templates/project-knowledge/{name}.md' for name in (
                'INDEX', 'HANDOFF', 'LESSONS', 'DECISIONS', 'UNRESOLVED', 'SOURCES')]]
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_markdown_local_links_resolve(self):
        for path in ROOT.rglob('*.md'):
            if '.git' in path.parts:
                continue
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                target = unquote(target.split('#')[0])
                if not target or '://' in target:
                    continue
                with self.subTest(file=str(path), target=target):
                    self.assertTrue((path.parent / target).exists())

    def test_frontmatter_and_legacy_prompt_variables(self):
        skill = (ROOT / 'skills/cad-continuity/SKILL.md').read_text(encoding='utf-8')
        frontmatter = skill.split('---', 2)[1]
        self.assertRegex(frontmatter, r'(?m)^name: cad-continuity$')
        self.assertRegex(frontmatter, r'(?m)^description: .+')
        for mode in ('ingest', 'audit'):
            prompt = (ROOT / f'prompts/{mode}.md').read_text(encoding='utf-8')
            self.assertIn('$ARGUMENTS', prompt)
            # Only ARGUMENTS may become a required named argument. Literal skill
            # references use the documented $$ escape.
            unescaped = prompt.replace('$$', '')
            self.assertEqual(set(re.findall(r'\$([A-Z][A-Z0-9_]*)', unescaped)), {'ARGUMENTS'})


if __name__ == '__main__':
    unittest.main()
