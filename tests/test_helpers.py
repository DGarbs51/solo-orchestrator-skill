import concurrent.futures
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
NAME = 'solo-orchestrator'


class Helpers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_command(self, *args, success=True):
        result = subprocess.run([str(x) for x in args], cwd=self.root,
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def setup_config(self, *args, success=True):
        return self.run_command('python3', ROOT / 'scripts/setup-opencode.py',
                                '--config-dir', self.root / 'config',
                                '--skill-dir', self.root / 'skill', *args, success=success)

    def test_config_preserves_settings_and_restores_previous(self):
        config = self.root / 'config/opencode.json'
        config.parent.mkdir()
        original = {'mcp': {'example': {'enabled': False}},
                    'permission': {'skill': {NAME: 'ask', 'other': 'allow'}}}
        config.write_text(json.dumps(original))
        config.chmod(0o640)
        self.setup_config()
        self.setup_config()
        installed = json.loads(config.read_text())
        self.assertEqual(installed['mcp'], original['mcp'])
        self.assertEqual(installed['permission']['skill'][NAME], 'deny')
        self.assertEqual(config.stat().st_mode & 0o777, 0o640)
        self.setup_config('--uninstall')
        restored = json.loads(config.read_text())
        self.assertEqual(restored['permission'], original['permission'])
        self.assertNotIn(NAME, restored['command'])

    def test_config_uninstall_preserves_user_edits(self):
        self.setup_config()
        config = self.root / 'config/opencode.json'
        value = json.loads(config.read_text())
        value['command'][NAME] = {'template': 'my custom command'}
        config.write_text(json.dumps(value))
        self.setup_config(success=False)
        self.setup_config('--uninstall')
        self.assertEqual(json.loads(config.read_text())['command'][NAME], value['command'][NAME])

    def test_interrupted_first_config_install_can_resume(self):
        self.setup_config()
        config = self.root / 'config/opencode.json'
        config.unlink()  # simulate state persisted before first config replacement
        self.setup_config()
        self.assertEqual(json.loads(config.read_text())['permission']['skill'][NAME], 'deny')

    def test_config_conflicts_are_not_overwritten(self):
        config = self.root / 'config/opencode.json'
        config.parent.mkdir()
        for value in ({'permission': 'ask'}, {'command': {NAME: {'template': 'custom'}}}):
            config.write_text(json.dumps(value))
            self.setup_config(success=False)
            self.assertEqual(json.loads(config.read_text()), value)
        (config.parent / 'opencode.jsonc').write_text('{}')
        self.setup_config(success=False)

    def cache(self, *args, success=True):
        result = self.run_command('python3', ROOT / 'scripts/routing-cache.py',
                                 '--db', self.root / 'cache.sqlite3', *args, success=success)
        return json.loads(result.stdout) if success else result

    def observation(self, name, offset, **overrides):
        value = {'observed_at': (datetime.now(timezone.utc) + timedelta(seconds=offset)).isoformat(),
                 'source': 'test', 'data': {'remaining': name}}
        value.update(overrides)
        path = self.root / f'{name}.json'
        path.write_text(json.dumps(value))
        return path

    def test_cache_freshness_history_and_invalid_observations(self):
        self.assertEqual(self.cache('get', 'usage', 'pool')['status'], 'missing')
        self.assertFalse((self.root / 'cache.sqlite3').exists())
        recent = self.observation('recent', -10)
        old = self.observation('old', -8000)
        self.cache('put', 'usage', 'pool', '--file', recent)
        self.assertEqual(self.cache('put', 'usage', 'pool', '--file', old)['status'], 'kept_existing')
        self.assertEqual(self.cache('get', 'usage', 'pool')['status'], 'fresh')
        self.assertEqual(len(self.cache('history', 'usage', 'pool')['observations']), 2)
        self.assertEqual(len(self.cache('history', 'usage', 'pool', '--limit', 1)['observations']), 1)
        for kind, expected in [('catalog', 'stale'), ('usage', 'stale'), ('outcome', 'historical')]:
            self.cache('put', kind, 'old', '--file', old)
            self.assertEqual(self.cache('get', kind, 'old')['status'], expected)
        for invalid in (None, 42, 'no date', '2026-01-01'):
            path = self.observation('bad', 0, observed_at=invalid)
            result = self.cache('put', 'usage', 'pool', '--file', path, success=False)
            self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(self.cache('get', 'usage', 'pool')['observation']['data']['remaining'], 'recent')
        self.cache('list', 'usage', '--limit', 0, success=False)

    def test_concurrent_cache_updates_keep_newest(self):
        paths = [self.observation(str(i), -100 + i) for i in range(12)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as workers:
            list(workers.map(lambda path: self.cache('put', 'usage', 'pool', '--file', path), paths))
        self.assertEqual(self.cache('get', 'usage', 'pool')['observation']['data']['remaining'], '11')
        self.assertEqual(len(self.cache('history', 'usage', 'pool')['observations']), 12)

    def install(self, *args, success=True):
        return self.run_command('bash', ROOT / 'install.sh', '--project', *args, success=success)

    def test_install_copy_is_complete_and_owned_uninstall(self):
        self.install('--targets', 'all', '--copy')
        for host in ('.claude', '.agents', '.cursor', '.opencode'):
            skill = self.root / host / 'skills' / NAME
            for resource in ('SKILL.md', 'references/worker-clis.md',
                             'agents/openai.yaml', 'scripts/routing-cache.py'):
                self.assertTrue((skill / resource).exists(), resource)
        self.install('--targets', 'opencode', '--uninstall')
        config = self.root / 'opencode.json'
        self.assertIn(NAME, json.loads(config.read_text())['command'])
        self.install('--targets', 'all', '--uninstall', '--force')
        self.assertNotIn(NAME, json.loads(config.read_text())['command'])
        self.assertFalse((self.root / '.agents/skills' / NAME).exists())

    def test_failed_opencode_setup_does_not_expose_skill(self):
        (self.root / 'opencode.jsonc').write_text('{}')
        self.install('--targets', 'opencode', success=False)
        self.assertFalse((self.root / '.opencode/skills' / NAME).is_symlink())

    def test_install_rejects_invalid_targets_before_mutation(self):
        self.install('--targets', 'claude,invalid', success=False)
        self.assertFalse((self.root / '.claude').exists())

    def test_install_link_repeats_and_preserves_foreign_link(self):
        self.install('--targets', 'opencode')
        self.install('--targets', 'opencode')
        self.install('--targets', 'opencode', '--uninstall')
        skill = self.root / '.opencode/skills' / NAME
        skill.symlink_to(self.root / 'foreign')
        self.install('--targets', 'opencode', '--uninstall')
        self.assertTrue(skill.is_symlink())


if __name__ == '__main__':
    unittest.main()
