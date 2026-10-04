"""Package the offline ARC solver as a private CPU Kaggle Notebook."""

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COMPETITION = 'arc-prize-2026-arc-agi-2'


def prepare(owner):
    if not re.fullmatch(r'[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*', owner):
        raise ValueError('owner must be a Kaggle username')
    competition = ROOT / 'competitions' / COMPETITION
    source = (competition / 'src/solver.py').read_text()
    code = (
        'from pathlib import Path\nimport importlib.util\n'
        f'SOURCE = {source!r}\n'
        "path = Path('/kaggle/working/solver.py')\npath.write_text(SOURCE)\n"
        "spec = importlib.util.spec_from_file_location('arc_solver', path)\n"
        'solver = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(solver)\n'
        "# In scoring runs Kaggle replaces the test challenges with hidden tasks.\n"
        "# Infer from the supplied demonstrations; never read test/evaluation solutions.\n"
        "metrics = solver.run(Path('/kaggle/input'), Path('/kaggle/working'), validate=False)\n"
    )
    notebook = {'nbformat': 4, 'nbformat_minor': 4, 'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}},
        'cells': [
            {'cell_type': 'markdown', 'metadata': {}, 'source': [
                '# ARC AGI 2 Symbolic Baseline\nOffline CPU rule search; two guesses per test grid. '
                'No pretrained models, external API calls, task-ID lookup, or solution-file access during inference.']},
            {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': [code]},
        ]}
    name = 'symbolic-baseline.ipynb'
    destination = competition / 'notebooks' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(notebook, indent=2) + '\n'
    destination.write_text(text)
    upload = ROOT / 'runs' / COMPETITION / 'kaggle-symbolic-baseline'
    upload.mkdir(parents=True, exist_ok=True)
    (upload / name).write_text(text)
    metadata = {'id': f'{owner}/arc-agi-2-symbolic-baseline', 'title': 'ARC AGI 2 Symbolic Baseline',
                'code_file': name, 'language': 'python', 'kernel_type': 'notebook',
                'is_private': 'true', 'enable_gpu': 'false', 'enable_internet': 'false',
                'dataset_sources': [], 'competition_sources': [COMPETITION],
                'kernel_sources': [], 'model_sources': []}
    (upload / 'kernel-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Prepared: {upload.relative_to(ROOT)}')
    return upload


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', required=True)
    args = parser.parse_args()
    prepare(args.owner)
