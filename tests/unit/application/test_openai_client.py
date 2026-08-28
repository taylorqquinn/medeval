"""Unit tests for OpenAIClient behavior in absence of the openai package.

These tests are careful to avoid requiring network or the OpenAI package. If the
openai package is installed in the environment, the test is skipped to avoid creating
external dependencies in CI.
"""

import os
import sys
import pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT,'src')
if SRC not in sys.path:
    sys.path.insert(0,SRC)

import medeval.application.openai_client as openai_client


def test_openai_client_requires_openai_package():
    """When the openai package is not available, OpenAIClient.__init__ should raise.

    If openai is installed in the test environment, skip this test to avoid external dependencies.
    """
    if getattr(openai_client, 'openai', None) is not None:
        pytest.skip("openai package present; skipping OpenAIClient init test")
    with pytest.raises(RuntimeError):
        openai_client.OpenAIClient()
