"""Read one submission's error field, omitted by the standard CLI table.

Invoke through kaggle_cli.py competitions submission-detail ID [--output PATH].
"""
import argparse
import json
from pathlib import Path


def details(response):
    status = str(response.status)
    failed = bool(response.error_description) or status.split(".")[-1] == "ERROR"
    return dict(ref=response.ref, status=status, scoring_failed=failed,
                error_description=response.error_description, public_score=response.public_score,
                description=response.description, url=response.url)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission_id", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    from kaggle.api.kaggle_api_extended import KaggleApi
    from kagglesdk.competitions.types.competition_api_service import ApiGetSubmissionRequest
    api = KaggleApi()
    api.authenticate()
    request = ApiGetSubmissionRequest()
    request.ref = args.submission_id
    with api.build_kaggle_client() as client:
        result = details(client.competitions.competition_api_client.get_submission(request))
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
