"""Verify algorithm replacement and standalone packaging of split modules."""

import csv
from contextlib import contextmanager
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest

ROOT = Path(__file__).resolve().parents[1]
NLP = ROOT / 'competitions/word2vec-nlp-tutorial'
ARC = ROOT / 'competitions/arc-prize-2026-arc-agi-2'
if not (NLP / 'src/pipeline.py').exists() or not (ARC / 'src/pipeline.py').exists():
    raise unittest.SkipTest('Private competition implementations are not present')


def script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def registered_module(module):
    # Remove only this fake module; ML libraries may import other modules lazily.
    previous = sys.modules.get(module.__name__)
    sys.modules[module.__name__] = module
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop(module.__name__, None)
        else:
            sys.modules[module.__name__] = previous


def sentiment_data(data):
    data.mkdir()
    for name, fields, rows in (
        ('labeledTrainData.tsv', ['id', 'sentiment', 'review'],
         [(str(i), i % 2, ('good movie' if i % 2 else 'bad movie') + f' unique{chr(97 + i)}') for i in range(20)]),
        ('testData.tsv', ['id', 'review'], [('a', 'good'), ('b', 'bad')]),
        ('sampleSubmission.csv', ['id', 'sentiment'], [('b', 0), ('a', 0)]),
    ):
        with (data / name).open('w', newline='') as stream:
            writer = csv.writer(stream, delimiter=',' if name.endswith('.csv') else '\t')
            writer.writerow(fields)
            writer.writerows(rows)


class PipelineComponentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        sentiment_data(self.data)

    def test_tfidf_reuses_scoring_and_submission_without_importing_torch(self):
        config = json.loads((NLP / 'config.json').read_text())
        config.update(model='tfidf_logistic', device='cpu')
        out = self.root / 'tfidf'
        code = (
            'import sys, importlib, importlib.abc, json\nfrom pathlib import Path\n'
            'class NoTorch(importlib.abc.MetaPathFinder):\n'
            '    def find_spec(self, fullname, path=None, target=None):\n'
            '        if fullname == "torch" or fullname.startswith("torch."):\n'
            '            raise ModuleNotFoundError("PyTorch unavailable in this test")\n'
            'sys.meta_path.insert(0, NoTorch())\n'
            f'sys.path.insert(0, {str(ROOT)!r})\n'
            'training = importlib.import_module("competitions.word2vec-nlp-tutorial.src.train")\n'
            f'training.run({config!r}, Path({str(self.data)!r}), Path({str(out)!r}))\n'
            'assert "torch" not in sys.modules\n'
        )
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((out / 'best-model.joblib').exists())
        self.assertFalse((out / 'best-model.pt').exists())
        split = json.loads((out / 'split.json').read_text())
        import joblib
        vocabulary = joblib.load(out / 'best-model.joblib')[0].vocabulary_
        for identifier in split['validation_ids']:
            self.assertNotIn('unique' + chr(97 + int(identifier)), vocabulary)
        with (out / 'submission.csv').open() as stream:
            self.assertEqual([row['id'] for row in csv.DictReader(stream)], ['b', 'a'])

    def test_invalid_probability_shape_and_range_are_rejected(self):
        pipeline = importlib.import_module('competitions.word2vec-nlp-tutorial.src.pipeline')
        class InvalidEstimator:
            def predict(self, texts):
                return [1.2] * len(texts)
        with self.assertRaises(ValueError):
            pipeline.probabilities(InvalidEstimator(), ['text'])

    def test_network_class_reuses_existing_preprocessing_and_training(self):
        backend = importlib.import_module('competitions.word2vec-nlp-tutorial.src.models.embedding_bag')
        pipeline = importlib.import_module('competitions.word2vec-nlp-tutorial.src.pipeline')
        class MyNetwork(backend.SentimentModel):
            def __init__(self, config):
                super().__init__(config['num_embeddings'], config)
                self.classifier = backend.nn.Linear(config['embedding_dim'], 1)
        module_name = pipeline.__package__ + '.models.test_network'
        module = ModuleType(module_name)
        module.MyNetwork = MyNetwork
        config = json.loads((NLP / 'config.json').read_text())
        config.update(device='cpu', epochs=1, network='models.test_network:MyNetwork')
        with registered_module(module):
            metrics = pipeline.run(config, self.data, self.root / 'custom-network')
        self.assertEqual(metrics['test_rows'], 2)
        self.assertTrue((self.root / 'custom-network/best-model.pt').exists())
        self.assertTrue((self.root / 'custom-network/submission.csv').exists())

    def test_arc_task_solver_can_change_without_changing_io_or_validation(self):
        pipeline = importlib.import_module('competitions.arc-prize-2026-arc-agi-2.src.pipeline')
        class IdentitySolver:
            device = 'cpu'
            def __init__(self, config):
                self.config = config
            def solve(self, task):
                return [{'attempt_1': row['input'], 'attempt_2': row['input']} for row in task['test']], 0
        challenges = {'example': {'train': [], 'test': [{'input': [[1, 2]]}]}}
        (self.data / 'arc-agi_test_challenges.json').write_text(json.dumps(challenges))
        (self.data / 'arc-agi_evaluation_challenges.json').write_text(json.dumps(challenges))
        (self.data / 'arc-agi_evaluation_solutions.json').write_text(json.dumps({'example': [[[1, 2]]]}))
        module_name = pipeline.__package__ + '.models.test_identity'
        module = ModuleType(module_name)
        module.IdentitySolver = IdentitySolver
        with registered_module(module):
            metrics = pipeline.run(self.data, self.root / 'arc-output', validate=True,
                                   config={'solver': 'models.test_identity:IdentitySolver'})
        self.assertEqual(metrics['public_evaluation']['exact_match_pass_at_2'], 1.0)
        submission = json.loads((self.root / 'arc-output/submission.json').read_text())
        self.assertEqual(submission['example'][0]['attempt_1'], [[1, 2]])

    def test_dedicated_notebooks_run_with_only_bundled_modules(self):
        shutil.copytree(ROOT / 'harness', self.root / 'harness', ignore=shutil.ignore_patterns('__pycache__'))
        for comp in (NLP, ARC):
            destination = self.root / 'competitions' / comp.name
            shutil.copytree(comp / 'src', destination / 'src', ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copy(comp / 'config.json', destination / 'config.json')
        builder = script('build_training_notebook')
        path = builder.build(self.root / 'competitions' / NLP.name)
        notebook = json.loads(path.read_text())
        codes = [''.join(cell['source']) for cell in notebook['cells'] if cell['cell_type'] == 'code']
        codes.insert(1, "CONFIG.update(device='cpu', epochs=1, embedding_dim=8, hidden_dim=8)")
        arc_builder = script('prepare_arc_notebook')
        arc_builder.ROOT = self.root
        upload = arc_builder.prepare('testuser')
        arc_notebook = json.loads((upload / 'symbolic-baseline.ipynb').read_text())
        arc_codes = [''.join(cell['source']) for cell in arc_notebook['cells'] if cell['cell_type'] == 'code']
        (self.data / 'arc-agi_test_challenges.json').write_text(json.dumps(
            {'example': {'train': [], 'test': [{'input': [[1]]}]}}))
        for name, cells, artifact in [('nlp', codes, 'submission.csv'), ('arc', arc_codes, 'submission.json')]:
            working = self.root / name
            working.mkdir()
            code = '\n'.join(cells).replace('/kaggle/working', str(working)).replace('/kaggle/input', str(self.data))
            result = subprocess.run([sys.executable, '-c', code], cwd=self.root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(list(working.rglob(artifact))), 1)
