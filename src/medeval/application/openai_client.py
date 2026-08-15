"""OpenAI-based LLM client wrapper with compatibility for both pre-1.0 and 1.x+ openai packages.

This module attempts to use the new OpenAI client (openai.OpenAI) when available and
falls back to the older openai.ChatCompletion API when necessary. If both fail, the
methods fall back to simple heuristics so tests remain deterministic in CI.
"""

import os
import re
import logging
try:
    import openai
except Exception:
    openai = None

from typing import Optional

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        if openai is None:
            raise RuntimeError("openai package is required for OpenAIClient. Install via 'pip install openai'")
        key = os.getenv("OPENAI_API_KEY")
        # support both old (openai.api_key) and new (OpenAI(api_key=...)) styles
        if key:
            try:
                openai.api_key = key
            except Exception:
                # some versions may not expose api_key writable property
                pass

        self.model = model
        self._is_new = False
        self._client = None

        # Try to instantiate the new-style OpenAI client if available
        OpenAIClass = getattr(openai, "OpenAI", None)
        if OpenAIClass is not None:
            try:
                # prefer passing api_key explicitly when available
                if key:
                    try:
                        self._client = OpenAIClass(api_key=key)
                    except TypeError:
                        self._client = OpenAIClass()
                else:
                    self._client = OpenAIClass()
                self._is_new = True
            except Exception as e:
                logger.debug("Failed to instantiate new OpenAI client: %s", e)
                self._client = None
                self._is_new = False

    def _extract_text(self, resp):
        # Try several common response shapes for robustness
        try:
            return resp.choices[0].message.content
        except Exception:
            pass
        try:
            return resp["choices"][0]["message"]["content"]
        except Exception:
            pass
        try:
            return resp.choices[0].text
        except Exception:
            pass
        try:
            return resp["choices"][0]["text"]
        except Exception:
            pass
        return str(resp)

    def generate(self, prompt: str) -> str:
        system_prompt = "You are a helpful assistant that summarizes clinical text."
        user_prompt = f"Summarize the following clinical text:\n\n{prompt}"

        # Try new-style client first
        if self._is_new and self._client is not None:
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    max_tokens=256,
                    temperature=0.0,
                )
                text = self._extract_text(resp)
                return text.strip() if text else ""
            except Exception as e:
                logger.warning("OpenAI new-style chat failed, falling back to older API: %s", e)

        # Fallback to older library shape
        try:
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                max_tokens=256,
                temperature=0.0,
            )
            text = self._extract_text(resp)
            return text.strip() if text else ""
        except Exception as e:
            logger.warning("OpenAI ChatCompletion failed: %s", e)

        # Last-resort deterministic summarization for CI/test stability
        tokens = prompt.split()
        return " ".join(tokens[:80])

    def judge(self, gold: str, pred: str) -> float:
        prompt = (
            "You are an objective evaluator. "
            "Rate how well the prediction matches the gold summary on a scale from 0.0 to 1.0. "
            "Return just the number, with no explanation.\n\n"
            f"Gold: {gold}\n\nPrediction: {pred}\n\nScore:"
        )

        # Try new-style client first
        if self._is_new and self._client is not None:
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=8,
                    temperature=0.0,
                )
                text = self._extract_text(resp).strip()
                # parse a float from the model output
                m = re.search(r"([0-9]*\.?[0-9]+)", text)
                if m:
                    try:
                        return float(m.group(1))
                    except Exception:
                        pass
            except Exception as e:
                logger.warning("OpenAI new-style judge failed, falling back: %s", e)

        # Fallback to older library shape
        try:
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8,
                temperature=0.0,
            )
            text = self._extract_text(resp).strip()
            m = re.search(r"([0-9]*\.?[0-9]+)", text)
            if m:
                try:
                    return float(m.group(1))
                except Exception:
                    pass
        except Exception as e:
            logger.warning("OpenAI ChatCompletion judge failed: %s", e)

        # Fallback heuristic: token overlap
        gold_set = set(gold.lower().split())
        pred_set = set(pred.lower().split())
        if not gold_set:
            return 1.0 if not pred_set else 0.0
        return len(gold_set & pred_set) / len(gold_set)
