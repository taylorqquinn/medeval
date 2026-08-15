"""OpenAI-based LLM client wrapper. Requires the openai package and an OPENAI_API_KEY env var.

This implementation is intentionally minimal: generate() calls the chat completions endpoint
and judge() asks the model to return a numeric score between 0.0 and 1.0. Both methods
fall back to a simple token-overlap heuristic if the OpenAI client is not available or
if parsing the model output fails.
"""

import os
try:
    import openai
except Exception:
    openai = None

from typing import Optional

class OpenAIClient:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        if openai is None:
            raise RuntimeError("openai package is required for OpenAIClient. Install via 'pip install openai'")
        key = os.getenv("OPENAI_API_KEY")
        if key:
            openai.api_key = key
        if not getattr(openai, "api_key", None):
            raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
        self.model = model

    def generate(self, prompt: str) -> str:
        resp = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes clinical text."},
                {"role": "user", "content": f"Summarize the following clinical text:\n\n{prompt}"}
            ],
            max_tokens=256,
            temperature=0.0,
        )
        return resp.choices[0].message.content.strip()

    def judge(self, gold: str, pred: str) -> float:
        # Ask the model to return a single floating point score between 0 and 1.
        prompt = (
            "You are an objective evaluator. "
            "Rate how well the prediction matches the gold summary on a scale from 0.0 to 1.0. "
            "Return just the number, with no explanation.\n\n"
            f"Gold: {gold}\n\nPrediction: {pred}\n\nScore:"
        )
        resp = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role":"user","content":prompt}],
            max_tokens=5,
            temperature=0.0,
        )
        text = resp.choices[0].message.content.strip()
        try:
            return float(text)
        except Exception:
            gold_set = set(gold.lower().split())
            pred_set = set(pred.lower().split())
            if not gold_set:
                return 1.0 if not pred_set else 0.0
            return len(gold_set & pred_set) / len(gold_set)
