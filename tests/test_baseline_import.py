"""Check public baseline selection and private copies without running downloaded code."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.import_kaggle_baseline import adapt_competition_paths, candidates, kernel_reference, prepare


class BaselineImportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for slug in ('titanic', 'custom-contest'):
            (self.root / 'competitions' / slug).mkdir(parents=True)

    def pull(self, reference, original, competition='titanic', code_file='source.ipynb'):
        metadata = {
            'id': reference, 'id_no': 123, 'code_file': code_file,
            'language': 'python', 'competition_sources': [competition],
            'dataset_sources': ['author/data'], 'kernel_sources': ['author/helper'],
            'model_sources': [], 'is_private': 'false', 'enable_internet': 'true',
        }
        notebook = {'nbformat': 4, 'nbformat_minor': 4,
                    'metadata': {'authors': [{'name': 'Original author'}], 'license': 'MIT'},
                    'cells': [{'cell_type': 'code', 'metadata': {}, 'execution_count': 7,
                               'outputs': [{'output_type': 'stream', 'name': 'stdout', 'text': 'saved'}],
                               'source': ['raise RuntimeError("must not execute")\n',
                                          '# create submission.csv\n']}]}
        (original / 'kernel-metadata.json').write_text(json.dumps(metadata))
        if code_file == 'source.ipynb':
            (original / code_file).write_text(json.dumps(notebook))
        elif code_file == 'source.py':
            (original / code_file).write_text('raise RuntimeError("must not execute")\n')

    def prepare(self, slug='titanic', reference=None, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return prepare(self.root, slug, reference, 'newuser', **kwargs)

    def test_automatic_starter_retains_code_and_provenance_without_publishing(self):
        references = []

        def pull(ref, path):
            references.append(ref)
            self.pull(ref, path)

        upload = self.prepare(pull=pull)
        self.assertEqual(references, ['alexisbcook/titanic-tutorial'])
        self.assertEqual({p.name for p in upload.iterdir()}, {'baseline.ipynb', 'kernel-metadata.json'})
        metadata = json.loads((upload / 'kernel-metadata.json').read_text())
        self.assertEqual(metadata['id'], 'newuser/titanic-baseline')
        self.assertNotIn('id_no', metadata)
        self.assertEqual(metadata['is_private'], 'true')
        self.assertEqual(metadata['enable_gpu'], 'false')
        self.assertEqual(metadata['enable_internet'], 'false')
        self.assertEqual(metadata['dataset_sources'], ['author/data'])
        notebook = json.loads((upload / 'baseline.ipynb').read_text())
        self.assertEqual(notebook['metadata']['license'], 'MIT')
        self.assertEqual(notebook['cells'][1]['outputs'], [])
        self.assertIsNone(notebook['cells'][1]['execution_count'])
        self.assertIn('must not execute', ''.join(notebook['cells'][1]['source']))
        editable = self.root / 'competitions/titanic/notebooks/baselines/baseline'
        origin = json.loads((editable / 'origin.json').read_text())
        self.assertEqual(origin['selection'], 'automatic')
        self.assertEqual(len(origin['source_sha256']), 64)
        original = json.loads((self.root / origin['original_directory'] / 'source.ipynb').read_text())
        self.assertTrue(original['cells'][0]['outputs'])
        with self.assertRaises(FileExistsError):
            self.prepare(pull=pull)
        self.assertEqual(len(references), 1)

    def test_other_competition_search_skips_unrelated_candidate(self):
        items = [
            {'ref': 'author/unrelated-baseline', 'title': 'baseline starter', 'totalVotes': 10},
            {'ref': 'author/matching-baseline', 'title': 'baseline', 'totalVotes': 2},
        ]
        calls = []

        def pull(ref, path):
            calls.append(ref)
            self.pull(ref, path, competition='custom-contest' if 'matching' in ref else 'titanic')

        upload = self.prepare('custom-contest', pull=pull, list_kernels=lambda slug: items)
        self.assertEqual(calls, [item['ref'] for item in items])
        self.assertEqual(json.loads((upload / 'kernel-metadata.json').read_text())['competition_sources'],
                         ['custom-contest'])
        with self.assertRaisesRegex(RuntimeError, 'No baseline candidate'):
            candidates(self.root, 'custom-contest', lambda slug: [])

    def test_explicit_versioned_script_becomes_gpu_notebook(self):
        upload = self.prepare(reference='https://www.kaggle.com/code/author/script/3', device='cuda',
                              pull=lambda ref, path: self.pull(ref, path, code_file='source.py'))
        metadata = json.loads((upload / 'kernel-metadata.json').read_text())
        self.assertEqual(metadata['machine_shape'], 'NvidiaTeslaT4')
        self.assertEqual(metadata['enable_gpu'], 'true')
        notebook = json.loads((upload / 'baseline.ipynb').read_text())
        self.assertEqual(notebook['cells'][1]['source'], ['raise RuntimeError("must not execute")\n'])

    def test_downloaded_path_cannot_escape_import_directory(self):
        with self.assertRaisesRegex(ValueError, 'within the import directory'):
            self.prepare(reference='author/notebook',
                         pull=lambda ref, path: self.pull(ref, path, code_file='../outside.py'))
        self.assertFalse((self.root / 'runs/titanic/notebooks/baseline').exists())

    def test_reference_validation(self):
        self.assertEqual(kernel_reference('author/notebook/2'), 'author/notebook/2')
        for value in ('https://example.com/code/author/notebook', 'author/../notebook',
                      'https://www.kaggle.com/competitions/titanic',
                      'https://www.kaggle.com/code/author/notebook?scriptVersionId=2'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                kernel_reference(value)

    def test_literal_input_paths_use_available_mount_without_changing_comments(self):
        for mount in ('competitions/titanic', 'titanic'):
            with self.subTest(mount=mount):
                root = self.root / mount
                root.mkdir(parents=True, exist_ok=True)
                (root / 'train.csv').write_text('PassengerId,Survived\n1,0\n')
                source = ('# Original path: /kaggle/input/titanic/train.csv\n'
                          'old = "/kaggle/input/titanic/train.csv"\n'
                          'current = "/kaggle/input/competitions/titanic/train.csv"\n'
                          'other = "/kaggle/input/other-contest/train.csv"\n')
                notebook = {'cells': [{'cell_type': 'markdown', 'source': ['Original author']},
                                      {'cell_type': 'code', 'source': [source]}]}
                self.assertEqual(adapt_competition_paths(notebook, 'titanic'), 2)
                namespace = {}
                exec(''.join(notebook['cells'][0]['source']), namespace)
                namespace['Path'] = lambda path: self.root / path.removeprefix('/kaggle/input/')
                exec(''.join(notebook['cells'][2]['source']), namespace)
                self.assertTrue(Path(namespace['old']).is_file())
                self.assertEqual(namespace['old'], namespace['current'])
                self.assertEqual(namespace['other'], '/kaggle/input/other-contest/train.csv')
                self.assertIn('# Original path: /kaggle/input/titanic/train.csv', ''.join(notebook['cells'][2]['source']))
                self.assertEqual(adapt_competition_paths(notebook, 'titanic'), 0)
                (root / 'train.csv').unlink()
                with self.assertRaisesRegex(FileNotFoundError, 'Competition input not found'):
                    namespace['_kh_competition_file']('train.csv')


if __name__ == '__main__':
    unittest.main()
