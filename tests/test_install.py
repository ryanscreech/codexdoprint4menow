import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PWSH = os.environ.get('CAD_TEST_POWERSHELL') or shutil.which('pwsh') or shutil.which('powershell')


@unittest.skipUnless(PWSH, 'PowerShell unavailable; installer behaviour not tested')
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.user = self.root / 'user [test]'
        self.project = self.root / 'project [test]'
        self.project.mkdir()
        self.env = dict(os.environ, CODEX_HOME=str(self.user / 'custom-codex'))
        self.skill = self.user / '.agents/skills/cad-continuity'

    def run_install(self, *args, success=True):
        result = subprocess.run([PWSH, '-NoProfile', '-NonInteractive', '-File',
                                 str(ROOT / 'scripts/install.ps1'), '-UserRoot', str(self.user),
                                 *map(str, args)], env=self.env, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_whatif_writes_nothing(self):
        self.run_install('-WhatIf', '-LegacyPrompts', '-ProjectPath', self.project)
        self.assertFalse(self.user.exists())
        self.assertEqual(list(self.project.iterdir()), [])

    def test_fresh_install_and_repeat_is_noop(self):
        self.run_install('-LegacyPrompts')
        self.assertEqual((self.skill / 'SKILL.md').read_bytes(), (ROOT / 'skills/cad-continuity/SKILL.md').read_bytes())
        self.assertTrue((self.skill / 'scripts/index_sessions.py').is_file())
        self.assertTrue((self.user / 'custom-codex/prompts/ingest.md').is_file())
        self.run_install('-LegacyPrompts')
        self.assertEqual(list((self.user / '.cad-continuity-backups').iterdir()), [])

    def test_modified_skill_requires_force_and_backup_is_outside_discovery(self):
        self.run_install()
        (self.skill / 'SKILL.md').write_text('custom rules', encoding='utf-8')
        self.run_install('-LegacyPrompts', success=False)
        self.assertEqual((self.skill / 'SKILL.md').read_text(), 'custom rules')
        self.assertFalse((self.user / 'custom-codex').exists())
        self.run_install('-Force')
        backups = list((self.user / '.cad-continuity-backups').glob('*/previous/SKILL.md'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'custom rules')
        self.assertEqual(len(list((self.user / '.agents/skills').rglob('SKILL.md'))), 1)

    def test_invalid_project_has_no_side_effects(self):
        self.run_install('-ProjectPath', self.project / 'missing', success=False)
        self.assertFalse(self.user.exists())

    def test_project_local_and_preserved_knowledge(self):
        self.run_install('-ProjectLocal', '-ProjectPath', self.project)
        self.assertFalse(self.skill.exists())
        self.assertTrue((self.project / '.agents/skills/cad-continuity/SKILL.md').is_file())
        kb = self.project / 'cad-knowledge'
        (kb / 'HANDOFF.md').write_text('owner history', encoding='utf-8')
        self.run_install('-ProjectLocal', '-ProjectPath', self.project, '-Force')
        self.assertEqual((kb / 'HANDOFF.md').read_text(), 'owner history')
        self.assertFalse((kb / 'project-knowledge').exists())

    def test_projectlocal_requires_project(self):
        self.run_install('-ProjectLocal', success=False)
        self.assertFalse(self.user.exists())

    def test_conflicting_prompt_detected_before_skill_is_written(self):
        prompt = self.user / 'custom-codex/prompts/audit.md'
        prompt.parent.mkdir(parents=True)
        prompt.write_text('existing prompt', encoding='utf-8')
        self.run_install('-LegacyPrompts', success=False)
        self.assertFalse(self.skill.exists())
        self.assertFalse((prompt.parent / 'ingest.md').exists())
        self.assertEqual(prompt.read_text(), 'existing prompt')

    def test_kb_file_blocks_install_before_writes(self):
        (self.project / 'cad-knowledge').write_text('do not destroy', encoding='utf-8')
        self.run_install('-ProjectPath', self.project, success=False)
        self.assertFalse(self.user.exists())

    def check_failed_activation(self, partial=False):
        self.run_install()
        (self.skill / 'SKILL.md').write_text('custom rules', encoding='utf-8')
        wrapper = self.root / 'simulate-failure.ps1'
        wrapper.write_text('''param($Installer, $TestRoot)
function Move-Item {
  param($LiteralPath, $Destination)
  if ((Split-Path -Leaf $LiteralPath) -eq 'staged') {
    # PARTIAL
    throw 'simulated activation failure'
  }
  Microsoft.PowerShell.Management\\Move-Item -LiteralPath $LiteralPath -Destination $Destination
}
& $Installer -UserRoot $TestRoot -Force
'''.replace('# PARTIAL', '[IO.Directory]::CreateDirectory($Destination) | Out-Null' if partial else ''), encoding='utf-8')
        result = subprocess.run([PWSH, '-NoProfile', '-NonInteractive', '-File', str(wrapper),
                                 str(ROOT / 'scripts/install.ps1'), str(self.user)],
                                env=self.env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('simulated activation failure', result.stderr)
        self.assertEqual((self.skill / 'SKILL.md').read_text(), 'custom rules')
        self.assertEqual(len(list((self.user / '.cad-continuity-backups').glob('*/failed'))), int(partial))

    def test_failed_activation_restores_previous_installation(self):
        self.check_failed_activation()

    def test_partial_activation_preserved_and_previous_restored(self):
        self.check_failed_activation(partial=True)


if __name__ == '__main__':
    unittest.main()
