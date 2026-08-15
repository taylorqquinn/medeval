#!/usr/bin/env python3
"""Helper script used by CI to run the evaluation and write a results JSON file.

Exits with code 2 when the quality gate fails so CI can mark the build as failed.
"""
import argparse
import json
import os
import sys

from medeval.evaluation.runner import run

llm_client = None
if os.getenv('OPENAI_API_KEY'):
    try:
        from medeval.application.openai_client import OpenAIClient
        llm_client = OpenAIClient()
    except Exception as e:
        print(f"Warning: OpenAI client not available: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default='datasets/clinical_cases.jsonl')
    parser.add_argument('--baseline', default='baselines/production.json')
    parser.add_argument('--output', default='results.json')
    args = parser.parse_args()

    res = run(args.dataset, args.baseline, llm_client=llm_client)
    with open(args.output, 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=2)

    print(json.dumps(res, indent=2))

    if res.get('passed') is False:
        print('Quality gate failed', file=sys.stderr)
        sys.exit(2)
    sys.exit(0)

if __name__ == '__main__':
    main()
