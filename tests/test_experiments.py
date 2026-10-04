"""Verify custom implementations, isolated runs, and offline Notebook packaging."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from uuid import uuid4

from harness.experiments import entry_path, execute, load_config

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('experiment_packager', ROOT / 'scripts/prepare_experiment_notebook.py')
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.slug = 'custom-' + uuid4().hex[:8]
        self.competition = self.root / 'competitions' / self.slug
        src = self.competition / 'src'
        src.mkdir(parents=True)
        (src / '__init__.py').write_text('')
        (src / 'helpers.py').write_text('def calculate(value):\n    return value * 2\n')
        (src / 'custom.py').write_text(
            'from .helpers import calculate\n'
            'def run(config, data_dir, output_dir):\n'
            '    output_dir.mkdir(parents=True)\n'
            '    config.get("nested", {}).update({"changed": True})\n'
            '    value = calculate(config["value"])\n'
            '    (output_dir / "prediction.txt").write_text(str(value))\n'
            '    return {"diagnostic_value": value, "device": config["device"]}\n')
        (self.competition / 'config.json').write_text(json.dumps({'value': 3, 'device': 'cpu', 'nested': {}}))
        (self.competition / 'configs').mkdir()
        (self.competition / 'configs/other.json').write_text(json.dumps({'value': 7, 'device': 'cpu'}))
        shutil.copytree(ROOT / 'harness', self.root / 'harness', ignore=shutil.ignore_patterns('__pycache__'))

    def test_custom_module_relative_imports_and_independent_configs(self):
        results = []
        for config_path in ('config.json', 'configs/other.json'):
            config = load_config(self.competition, config_path)
            results.append(execute(self.root, self.slug, 'src/custom.py', config, 'my-model'))
            self.assertNotIn('changed', config.get('nested', {}))
        self.assertEqual([r['metrics']['diagnostic_value'] for r in results], [6, 14])
        self.assertEqual(results[0]['config']['nested'], {})
        self.assertNotEqual(results[0]['output_dir'], results[1]['output_dir'])
        for result in results:
            saved = json.loads((Path(result['output_dir']) / 'experiment.json').read_text())
            self.assertEqual(saved['entry'], 'src/custom.py')
            self.assertIn(f'competitions/{self.slug}/src/helpers.py', saved['source_sha256'])
            self.assertTrue((Path(result['output_dir']) / 'prediction.txt').is_file())
        with self.assertRaises(FileExistsError):
            execute(self.root, self.slug, 'src/custom.py', {'device': 'cpu'}, 'my-model',
                    output_dir=Path(results[0]['output_dir']))

    def test_notebook_runs_custom_code_without_credentials_or_local_data(self):
        (self.root / 'config').mkdir()
        (self.root / 'config/kaggle.local.json').write_text('secret-test-marker')
        (self.competition / 'requirements.txt').write_text('dependency-test-marker')
        (self.competition / 'notes.txt').write_text('notes-test-marker')
        bundle = PACKAGER.prepare(self.root, self.slug, 'testuser', 'src/custom.py',
                                  'configs/other.json', 'custom-test', 'cpu', 'prediction.txt')
        nb = json.loads((bundle / 'experiment.ipynb').read_text())
        code = ''.join(nb['cells'][1]['source'])
        self.assertNotIn('secret-test-marker', code)
        self.assertNotIn('dependency-test-marker', code)
        self.assertNotIn('notes-test-marker', code)
        self.assertEqual({p.name for p in bundle.iterdir()}, {'experiment.ipynb', 'kernel-metadata.json'})
        working = self.root / 'simulated-kaggle'
        working.mkdir()
        code = code.replace("/kaggle/working", str(working)).replace('/kaggle/input', str(self.root / 'input'))
        result = subprocess.run([sys.executable, '-c', code], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        outputs = list((working / 'experiments').rglob('experiment.json'))
        self.assertEqual(len(outputs), 1)
        self.assertEqual(json.loads(outputs[0].read_text())['metrics']['diagnostic_value'], 14)
        self.assertEqual((working / 'prediction.txt').read_text(), '14')

    def test_entry_and_config_cannot_escape_competition(self):
        for path in ('../escape.py', '/tmp/example.py', 'notebooks/example.py'):
            with self.assertRaises(ValueError):
                entry_path(self.competition, path)
        with self.assertRaises(ValueError):
            load_config(self.competition, '../../config/kaggle.local.json')
        (self.competition / 'src/linked.py').symlink_to(ROOT / 'scripts/kaggle_cli.py')
        with self.assertRaises(ValueError):
            entry_path(self.competition, 'src/linked.py')

    def test_non_finite_scores_are_not_saved_as_valid_experiments(self):
        (self.competition / 'src/invalid.py').write_text('def run(*args):\n    return {"score": float("nan")}\n')
        with self.assertRaises(ValueError):
            execute(self.root, self.slug, 'src/invalid.py', {'device': 'cpu'}, 'bad-score')

    def test_template_has_implementation_contract_and_excludes_download_markers(self):
        scratch = self.root / 'scaffold'
        scratch.mkdir()
        (scratch / 'scripts').mkdir()
        shutil.copy(ROOT / 'scripts/new_competition.py', scratch / 'scripts/new_competition.py')
        template = scratch / 'competitions/_template'
        shutil.copytree(ROOT / 'competitions/_template', template)
        (template / 'README.md:Zone.Identifier').write_text('download marker')
        result = subprocess.run([sys.executable, str(scratch / 'scripts/new_competition.py'), 'new-test'],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        created = scratch / 'competitions/new-test'
        self.assertTrue((created / 'src/experiment.py').is_file())
        self.assertTrue((created / 'configs/README.md').is_file())
        self.assertFalse(list(created.rglob('*Zone.Identifier*')))
        self.assertNotIn('__SLUG__', (created / 'README.md').read_text())
        again = subprocess.run([sys.executable, str(scratch / 'scripts/new_competition.py'), 'new-test'],
                               text=True, capture_output=True)
        self.assertNotEqual(again.returncode, 0)


if __name__ == '__main__':
    unittest.main()
