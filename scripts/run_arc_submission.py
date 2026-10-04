"""Execute the ARC code Notebook and optionally submit its pinned version once."""

import argparse
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import time

from prepare_arc_notebook import COMPETITION, ROOT, prepare
from kaggle_helpers import cli


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', required=True)
    parser.add_argument('--submit', action='store_true')
    parser.add_argument('--resume-version', type=int, help='Collect a previously pushed version without pushing again')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*', args.owner):
        parser.error('owner must be a Kaggle username')
    reference = f'{args.owner}/arc-agi-2-symbolic-baseline'
    version = args.resume_version
    if version is None:
        upload = prepare(args.owner)
        response = cli('kernels', 'push', '-p', str(upload), '--timeout', '1800')
        print(response, flush=True)
        match = re.search(r'Kernel version (\d+) successfully pushed', response)
        if not match:
            raise RuntimeError('Kaggle did not confirm a Notebook version')
        version = int(match.group(1))
    elif version <= 0:
        parser.error('resume-version must be positive')
    pinned = f'{reference}/{version}'
    deadline = time.monotonic() + 2400
    while True:
        status = cli('kernels', 'status', pinned)
        print(status, flush=True)
        if '"KernelWorkerStatus.COMPLETE"' in status:
            break
        if any(word in status.upper() for word in ('ERROR', 'CANCEL', 'FAILED')):
            raise RuntimeError(status)
        if time.monotonic() > deadline:
            raise TimeoutError('Notebook pending; resume with --resume-version')
        time.sleep(20)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = ROOT / 'runs' / COMPETITION / 'kaggle-results' / timestamp
    output.mkdir(parents=True, exist_ok=False)
    print(cli('kernels', 'output', pinned, '-p', str(output)), flush=True)
    submission = output / 'submission.json'
    if not submission.is_file():
        raise RuntimeError('Notebook did not produce submission.json')
    metrics = json.loads((output / 'metrics.json').read_text())
    print(json.dumps(metrics, indent=2), flush=True)
    result = {'notebook': reference, 'version': version, 'metrics': metrics, 'submitted': False}
    result_path = output / 'result.json'
    result_path.write_text(json.dumps(result, indent=2) + '\n')
    if args.submit:
        message = f'ARC symbolic baseline v{version} {timestamp}'
        result.update(submission_state='requested', submission_message=message)
        result_path.write_text(json.dumps(result, indent=2) + '\n')
        # Code competition: submit the Notebook version, not the local JSON upload.
        response = cli('competitions', 'submit', COMPETITION, '-k', reference,
                       '-v', str(version), '-f', 'submission.json', '-m', message)
        print(response, flush=True)
        result.update(submitted=True, submission_response=response, submission_state='sent')
        result_path.write_text(json.dumps(result, indent=2) + '\n')
        deadline = time.monotonic() + 1200
        while True:
            text = cli('competitions', 'submissions', COMPETITION, '--csv', '--page-size', '20')
            (output / 'submissions.csv').write_text(text + '\n')
            matches = [row for row in csv.DictReader(io.StringIO(text)) if row.get('description') == message]
            if matches:
                row = matches[0]
                print(json.dumps(row), flush=True)
                result['kaggle_submission'] = row
                score = row.get('publicScore', '')
                if score and score.lower() not in {'none', 'null', 'nan'}:
                    result['submission_state'] = 'scored'
                    result_path.write_text(json.dumps(result, indent=2) + '\n')
                    print(f'Kaggle public score: {score}', flush=True)
                    break
                result_path.write_text(json.dumps(result, indent=2) + '\n')
                if any(word in row.get('status', '').upper() for word in ('ERROR', 'FAILED')):
                    raise RuntimeError('Scoring failed; check submission error details on Kaggle')
            if time.monotonic() > deadline:
                print('Submitted once; score pending. Check submissions later without resubmitting.', flush=True)
                break
            time.sleep(20)
    print(f'Result: {result_path.relative_to(ROOT)}', flush=True)


if __name__ == '__main__':
    main()
