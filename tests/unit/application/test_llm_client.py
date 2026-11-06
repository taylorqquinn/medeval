"""Tests for the deterministic LLMClient used in unit tests."""

import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from medeval.application.llm_client import LLMClient


def test_llm_generate_and_judge():
    client = LLMClient()
    prompt = 'word ' * 200
    out = client.generate(prompt)
    assert isinstance(out, str)
    assert client.judge('', '') == pytest.approx(1.0)
    assert client.judge('a b c', '') == pytest.approx(0.0)
    assert client.judge('a b c', 'a') == pytest.approx(1/3)
