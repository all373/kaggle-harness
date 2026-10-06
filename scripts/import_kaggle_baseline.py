"""Pull an existing Kaggle Python baseline and prepare a private working copy.

Download and local preparation only. This command never runs or submits code.
"""

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tokenize
from urllib.parse import urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.artifacts import write_json
from harness.experiments import validate_slug

# Verified beginner starter; other competitions use Code search.
STARTERS = {'titanic': 'alexisbcook/titanic-tutorial'}


def adapt_competition_paths(notebook: dict, slug: str) -> int:
    """Resolve literal competition input paths across old and current mounts."""
    prefixes = (f'/kaggle/input/{slug}/', f'/kaggle/input/competitions/{slug}/')
    changed = 0
    for cell in notebook['cells']:
        if cell.get('cell_type') != 'code':
            continue
        source = cell.get('source', '')
        source = source if isinstance(source, str) else ''.join(source)
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        except (tokenize.TokenError, IndentationError):
            continue
        replacements = []
        lines = source.splitlines(keepends=True)
        offsets = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        for token in tokens:
            if token.type != tokenize.STRING:
                continue
            try:
                value = ast.literal_eval(token.string)
            except (ValueError, SyntaxError):
                continue
            if not isinstance(value, str):
                continue
            for prefix in prefixes:
                if value.startswith(prefix):
                    start = offsets[token.start[0] - 1] + token.start[1]
                    end = offsets[token.end[0] - 1] + token.end[1]
                    replacements.append((start, end, f'_kh_competition_file({value[len(prefix):]!r})'))
                    break
        for start, end, replacement in reversed(replacements):
            source = source[:start] + replacement + source[end:]
        if replacements:
            cell['source'] = source.splitlines(keepends=True)
            changed += len(replacements)
    if changed:
        helper = (
            '# Resolve competition inputs in current and legacy Kaggle environments.\n'
            'from pathlib import Path\n\n'
            'def _kh_competition_file(relative):\n'
            f'    roots = (Path("/kaggle/input/competitions/{slug}"), Path("/kaggle/input/{slug}"))\n'
            '    for root in roots:\n'
            '        candidate = root / relative\n'
            '        if candidate.exists():\n'
            '            return str(candidate)\n'
            '    raise FileNotFoundError(f"Competition input not found: {relative}; searched {roots}")\n'
        )
        notebook['cells'].insert(0, {
            'cell_type': 'code', 'metadata': {'tags': ['kaggle-harness-input-paths']},
            'execution_count': None, 'outputs': [], 'source': helper.splitlines(keepends=True),
        })
    return changed


def candidates(root: Path, slug: str, list_kernels=None) -> list[str]:
    if slug in STARTERS:
        return [STARTERS[slug]]
    if list_kernels is None:
        result = subprocess.run(
            [sys.executable, str(root / 'scripts/kaggle_cli.py'), 'kernels', 'list',
             '--competition', slug, '--language', 'python', '--kernel-type', 'notebook',
             '--sort-by', 'voteCount', '--page-size', '20', '--format', 'json'],
            text=True, capture_output=True, timeout=60,
        )
        if result.returncode:
            raise RuntimeError('Kaggle Code search failed:\n' + result.stdout + result.stderr)
        try:
            items = json.loads(result.stdout)
        except ValueError as error:
            raise RuntimeError('No searchable baseline was returned; use --kernel with a Code URL') from error
    else:
        items = list_kernels(slug)
    if not isinstance(items, list):
        raise ValueError('Expected a list of Kaggle Code candidates')
    ranked = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = str(item.get('title', '')).lower() + ' ' + str(item.get('ref', '')).lower()
        rank = sum(word in text for word in ('baseline', 'starter', 'tutorial', 'submission', 'benchmark'))
        if rank:
            try:
                reference = kernel_reference(item.get('ref', ''))
            except (ValueError, TypeError):
                continue
            ranked.append((-rank, -int(item.get('totalVotes', 0)), reference))
    references = list(dict.fromkeys(item[2] for item in sorted(ranked)))[:5]
    if not references:
        raise RuntimeError('No baseline candidate found for this competition; use --kernel with a Code URL')
    return references


def source_file(original: Path, metadata: dict) -> Path:
    relative = Path(metadata.get('code_file', ''))
    source = original / relative
    if (relative.is_absolute() or '..' in relative.parts or not source.is_file()
            or source.is_symlink() or not source.resolve().is_relative_to(original.resolve())):
        raise ValueError('Downloaded code_file must name a file within the import directory')
    return source


def kernel_reference(value: str) -> str:
    if '://' in value:
        url = urlsplit(value)
        if url.scheme != 'https' or url.hostname not in {'kaggle.com', 'www.kaggle.com'}:
            raise ValueError('Use a Kaggle Code HTTPS URL or owner/notebook[/version]')
        if not url.path.startswith('/code/'):
            raise ValueError('Use the Notebook URL under /code/, not a competition URL')
        if url.query or url.fragment:
            raise ValueError('Use a plain Code URL or owner/notebook/version to pin a version')
        value = url.path.removeprefix('/code/').strip('/')
    if not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+(?:/[1-9][0-9]*)?', value):
        raise ValueError('kernel must be owner/notebook or owner/notebook/version')
    return value


def prepare(root: Path, slug: str, reference: str | None, owner: str, name: str = 'baseline',
            device: str = 'cpu', pull=None, list_kernels=None) -> Path:
    validate_slug(slug)
    validate_slug(name)
    explicit = reference is not None
    if explicit:
        reference = kernel_reference(reference)
    if not re.fullmatch(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', owner):
        raise ValueError('owner must be your own Kaggle username')
    if device not in {'cpu', 'cuda'}:
        raise ValueError('device must be cpu or cuda')
    competition = root / 'competitions' / slug
    if not competition.is_dir() or slug == '_template':
        raise ValueError('Create the competition directory first with new_competition.py')
    editable = competition / 'notebooks' / 'baselines' / name
    upload = root / 'runs' / slug / 'notebooks' / name
    if editable.exists() or upload.exists():
        raise FileExistsError('Baseline or upload folder already exists; choose a new --name to preserve edits')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid4().hex[:8]
    references = [reference] if explicit else candidates(root, slug, list_kernels)
    for index, reference in enumerate(references):
        original = competition / 'notebooks' / 'imports' / name / run_id / f'candidate-{index + 1}'
        original.mkdir(parents=True)
        if pull is None:
            result = subprocess.run(
                [sys.executable, str(root / 'scripts/kaggle_cli.py'), 'kernels', 'pull',
                 reference, '-p', str(original), '-m'], text=True, capture_output=True, timeout=180,
            )
            if result.returncode:
                raise RuntimeError('Kaggle pull failed:\n' + result.stdout + result.stderr)
        else:
            pull(reference, original)
        metadata = json.loads((original / 'kernel-metadata.json').read_text())
        source = source_file(original, metadata)
        if metadata.get('language') != 'python':
            if explicit:
                raise ValueError('Choose a Python Notebook or script baseline')
            continue
        if not explicit:
            # Search may return unrelated Code; never use it based on title alone.
            text = source.read_text().lower()
            if slug not in metadata.get('competition_sources', []) or 'submission' not in text:
                continue
        break
    else:
        raise RuntimeError('No candidate with matching competition inputs and submission code was found; use --kernel')
    source_url = 'https://www.kaggle.com/code/' + reference
    if source.suffix == '.ipynb':
        notebook = json.loads(source.read_text())
        if notebook.get('nbformat') != 4 or not isinstance(notebook.get('cells'), list):
            raise ValueError('Expected a version 4 Python Notebook')
        for cell in notebook['cells']:
            if cell.get('cell_type') == 'code':
                cell['outputs'] = []
                cell['execution_count'] = None
        original_metadata = notebook.get('metadata', {})
        notebook['metadata'] = {field: original_metadata[field] for field in
                                ('authors', 'license', 'license_name') if field in original_metadata}
        notebook['metadata']['kernelspec'] = {
            'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
    elif source.suffix == '.py':
        notebook = {'nbformat': 4, 'nbformat_minor': 4, 'metadata': {'kernelspec': {
            'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}},
            'cells': [{'cell_type': 'code', 'metadata': {}, 'execution_count': None,
                       'outputs': [], 'source': [source.read_text()]}]}
    else:
        raise ValueError('Choose an .ipynb or .py baseline')
    adapted_paths = adapt_competition_paths(notebook, slug)
    notebook['cells'].insert(0, {'cell_type': 'markdown', 'metadata': {}, 'source': [
        f'# Imported baseline: {slug}\n\nSource: [{reference}]({source_url})\n\n'
        'Keep the original author attribution and comply with the source license. '
        'Review inputs, dependencies and output filename before running.\n']})
    new_metadata = {
        'id': f'{owner}/{slug}-{name}', 'title': f'{slug}-{name}'.replace('-', ' '),
        'code_file': 'baseline.ipynb', 'language': 'python', 'kernel_type': 'notebook',
        'is_private': 'true', 'enable_gpu': 'true' if device == 'cuda' else 'false',
        'enable_internet': 'false', 'competition_sources': [slug],
    }
    for field in ('dataset_sources', 'kernel_sources', 'model_sources'):
        inputs = metadata.get(field, [])
        if not isinstance(inputs, list) or not all(isinstance(value, str) for value in inputs):
            raise ValueError(f'Invalid source metadata: {field}')
        new_metadata[field] = inputs
    if device == 'cuda':
        new_metadata['machine_shape'] = 'NvidiaTeslaT4'
    editable.mkdir(parents=True)
    write_json(editable / 'baseline.ipynb', notebook)
    write_json(editable / 'kernel-metadata.json', new_metadata)
    write_json(editable / 'origin.json', {
        'reference': reference, 'source_url': source_url,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'downloaded_at': run_id, 'original_directory': str(original.relative_to(root)),
        'selection': 'explicit' if explicit else 'automatic',
        'adapted_input_paths': adapted_paths,
    })
    upload.mkdir(parents=True)
    for name in ('baseline.ipynb', 'kernel-metadata.json'):
        shutil.copyfile(editable / name, upload / name)
    print(f'Editable baseline: {editable}')
    print(f'Upload directory: {upload}')
    print(f'Private Notebook ID: {new_metadata["id"]}')
    print(f'Source: {source_url}')
    print('Downloaded and prepared locally. No code execution or submission was performed.')
    return upload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('competition')
    parser.add_argument('--kernel', help='Optional Code URL or owner/notebook[/version]; default: select by competition')
    parser.add_argument('--owner', required=True, help='Your own Kaggle username')
    parser.add_argument('--name', default='baseline')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    args = parser.parse_args()
    prepare(ROOT, args.competition, args.kernel, args.owner, args.name, args.device)


if __name__ == '__main__':
    main()
