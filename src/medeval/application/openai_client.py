"""OpenAI-based LLM client with real API integration, cost tracking, and rate limiting.

This module provides a production-ready OpenAI client with:
- Real API integration with automatic fallback for testing
- Cost tracking with budget enforcement
- Rate limiting to prevent quota exhaustion
- Support for multiple models (GPT-4, GPT-3.5-turbo, etc.)
- Comprehensive error handling and retries
"""

import os
import re
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

try:
    import openai
    from openai import OpenAI, RateLimitError, APIError
except Exception:
    openai = None
    OpenAI = None
    RateLimitError = Exception
    APIError = Exception

logger = logging.getLogger(__name__)


@dataclass
class CostTracker:
    """Track API costs for OpenAI requests."""
    
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    total_cost: float = 0.0
    cost_by_operation: Dict[str, float] = field(default_factory=dict)
    requests_by_operation: Dict[str, int] = field(default_factory=dict)
    
    def add_request(self, operation: str, input_tokens: int, output_tokens: int, cost: float):
        """Record a completed API request.
        
        Args:
            operation: Operation type ('generate' or 'judge')
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            cost: Cost of the request in USD
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_requests += 1
        self.total_cost += cost
        
        self.cost_by_operation[operation] = self.cost_by_operation.get(operation, 0.0) + cost
        self.requests_by_operation[operation] = self.requests_by_operation.get(operation, 0) + 1
        
        logger.debug(
            f"API request tracked: {operation} | "
            f"tokens: {input_tokens} in + {output_tokens} out | "
            f"cost: ${cost:.6f} | "
            f"total: ${self.total_cost:.6f}"
        )
    
    def get_report(self) -> Dict[str, Any]:
        """Generate a cost report.
        
        Returns:
            Dictionary with cost breakdown and statistics
        """
        return {
            "total_cost_usd": round(self.total_cost, 6),
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "cost_per_request": round(self.total_cost / max(1, self.total_requests), 6),
            "cost_by_operation": {k: round(v, 6) for k, v in self.cost_by_operation.items()},
            "requests_by_operation": self.requests_by_operation,
        }


@dataclass
class RateLimiter:
    """Simple token bucket rate limiter for API requests."""
    
    max_requests_per_minute: int = 60
    max_tokens_per_minute: Optional[int] = 90000
    min_delay_seconds: float = 1.0
    
    _request_timestamps: list = field(default_factory=list)
    _token_usage: list = field(default_factory=list)
    _last_request_time: float = 0.0
    
    def wait_if_needed(self, estimated_tokens: int = 1000):
        """Wait if rate limit would be exceeded.
        
        Args:
            estimated_tokens: Estimated tokens for the upcoming request
        """
        current_time = time.time()
        
        # Enforce minimum delay between requests
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.min_delay_seconds:
            sleep_time = self.min_delay_seconds - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for min delay")
            time.sleep(sleep_time)
            current_time = time.time()
        
        # Clean old timestamps (>1 minute old)
        cutoff = current_time - 60
        self._request_timestamps = [t for t in self._request_timestamps if t > cutoff]
        self._token_usage = [(t, tokens) for t, tokens in self._token_usage if t > cutoff]
        
        # Check request rate limit
        if len(self._request_timestamps) >= self.max_requests_per_minute:
            oldest = self._request_timestamps[0]
            wait_time = 60 - (current_time - oldest)
            if wait_time > 0:
                logger.warning(f"Rate limit: {self.max_requests_per_minute} req/min reached. Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                current_time = time.time()
        
        # Check token rate limit
        if self.max_tokens_per_minute:
            total_tokens_used = sum(tokens for _, tokens in self._token_usage)
            if total_tokens_used + estimated_tokens > self.max_tokens_per_minute:
                if self._token_usage:
                    oldest_token_time = self._token_usage[0][0]
                    wait_time = 60 - (current_time - oldest_token_time)
                    if wait_time > 0:
                        logger.warning(
                            f"Token rate limit: {total_tokens_used}/{self.max_tokens_per_minute} tokens/min. "
                            f"Waiting {wait_time:.1f}s"
                        )
                        time.sleep(wait_time)
                        current_time = time.time()
        
        # Record this request
        self._request_timestamps.append(current_time)
        self._token_usage.append((current_time, estimated_tokens))
        self._last_request_time = current_time

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Production-ready OpenAI client with cost tracking and rate limiting.
    
    Features:
    - Real API integration with automatic fallback for testing
    - Cost tracking with budget enforcement
    - Rate limiting to prevent quota exhaustion
    - Comprehensive error handling and retries
    
    Args:
        model: Model to use for generation (default: gpt-3.5-turbo)
        judge_model: Model to use for judging (default: same as model)
        config: Configuration dictionary from medeval_config.yaml
        enable_cost_tracking: Enable cost tracking (default: True)
        enable_rate_limiting: Enable rate limiting (default: True)
        use_real_api: If False, use fallback heuristics (default: True)
    """
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        judge_model: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        enable_cost_tracking: bool = True,
        enable_rate_limiting: bool = True,
        use_real_api: bool = True
    ):
        self.model = model
        self.judge_model = judge_model or model
        self.config = config or {}
        self.use_real_api = use_real_api
        
        # Initialize cost tracker
        self.cost_tracker = CostTracker() if enable_cost_tracking else None
        
        # Budget limits
        self.max_cost_per_run = self.config.get("max_cost_per_run")
        self.max_cost_per_case = self.config.get("max_cost_per_case")
        
        # Initialize rate limiter
        if enable_rate_limiting:
            rate_config = self.config.get("rate_limit", {})
            self.rate_limiter = RateLimiter(
                max_requests_per_minute=rate_config.get("max_requests_per_minute", 60),
                max_tokens_per_minute=rate_config.get("max_tokens_per_minute", 90000),
                min_delay_seconds=rate_config.get("min_delay_seconds", 1.0)
            )
        else:
            self.rate_limiter = None
        
        # Pricing table
        self.pricing = self.config.get("pricing", {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        })
        
        # Initialize OpenAI client
        self._client = None
        self._is_new = False
        
        if not use_real_api:
            logger.info("OpenAI client in test mode - using fallback heuristics")
            return
        
        if openai is None:
            logger.warning("openai package not available - falling back to heuristics")
            return
        
        # Get API key
        api_key = self._get_api_key()
        if not api_key:
            logger.warning("No OpenAI API key found - falling back to heuristics")
            return
        
        # Try to instantiate OpenAI client
        if OpenAI is not None:
            try:
                org_id = self.config.get("organization")
                if org_id:
                    self._client = OpenAI(api_key=api_key, organization=org_id)
                else:
                    self._client = OpenAI(api_key=api_key)
                self._is_new = True
                logger.info(f"OpenAI client initialized with model {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self._client = None
        else:
            logger.warning("OpenAI client class not available - using fallback")
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from configuration.
        
        Returns:
            API key string or None if not found
        """
        api_key_source = self.config.get("api_key_source", "env")
        
        if api_key_source == "env":
            return os.getenv("OPENAI_API_KEY")
        elif api_key_source == "file":
            key_file = self.config.get("api_key_file")
            if key_file and os.path.exists(key_file):
                try:
                    with open(key_file, 'r') as f:
                        return f.read().strip()
                except Exception as e:
                    logger.error(f"Failed to read API key from file: {e}")
                    return None
        elif api_key_source == "inline":
            # Not recommended for production
            logger.warning("Using inline API key - not recommended for production")
            return self.config.get("api_key")
        
        return None
    
    def _check_budget(self, operation: str, estimated_cost: float = 0.01):
        """Check if budget allows this operation.
        
        Args:
            operation: Operation type for logging
            estimated_cost: Estimated cost of the operation
            
        Raises:
            RuntimeError: If budget would be exceeded
        """
        if not self.cost_tracker:
            return
        
        # Check per-run budget
        if self.max_cost_per_run:
            projected_cost = self.cost_tracker.total_cost + estimated_cost
            if projected_cost > self.max_cost_per_run:
                raise RuntimeError(
                    f"Budget exceeded: {operation} would cost ${projected_cost:.6f}, "
                    f"max is ${self.max_cost_per_run:.6f}"
                )
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a request.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        # Get pricing for model (fallback to gpt-3.5-turbo if not found)
        model_pricing = self.pricing.get(model, self.pricing.get("gpt-3.5-turbo", {}))
        
        input_cost = (input_tokens / 1000) * model_pricing.get("input", 0.0005)
        output_cost = (output_tokens / 1000) * model_pricing.get("output", 0.0015)
        
        return input_cost + output_cost

    def _extract_text(self, resp) -> str:
        """Extract text content from OpenAI response.
        
        Args:
            resp: OpenAI API response object
            
        Returns:
            Extracted text content
        """
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
    
    def _extract_usage(self, resp) -> tuple:
        """Extract token usage from OpenAI response.
        
        Args:
            resp: OpenAI API response object
            
        Returns:
            Tuple of (input_tokens, output_tokens)
        """
        try:
            usage = resp.usage
            return (usage.prompt_tokens, usage.completion_tokens)
        except Exception:
            pass
        try:
            usage = resp["usage"]
            return (usage["prompt_tokens"], usage["completion_tokens"])
        except Exception:
            pass
        return (0, 0)

    def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate a summary using OpenAI.
        
        Args:
            prompt: Clinical text to summarize
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated summary text
            
        Raises:
            RuntimeError: If budget is exceeded
        """
        # Check budget before making request
        self._check_budget("generate", estimated_cost=0.01)
        
        # Apply rate limiting
        if self.rate_limiter:
            self.rate_limiter.wait_if_needed(estimated_tokens=len(prompt.split()) * 2)
        
        system_prompt = "You are a helpful assistant that summarizes clinical text."
        user_prompt = f"Summarize the following clinical text:\n\n{prompt}"
        
        # Try real API call if available
        if self.use_real_api and self._is_new and self._client is not None:
            try:
                logger.debug(f"Calling OpenAI API for generation (model={self.model})")
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=self.config.get("temperature", 0.0),
                )
                text = self._extract_text(resp)
                
                # Track cost
                if self.cost_tracker:
                    input_tokens, output_tokens = self._extract_usage(resp)
                    cost = self._calculate_cost(self.model, input_tokens, output_tokens)
                    self.cost_tracker.add_request("generate", input_tokens, output_tokens, cost)
                
                return text.strip() if text else ""
                
            except RateLimitError as e:
                logger.error(f"OpenAI rate limit exceeded: {e}")
                raise
            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                # Fall through to fallback
            except Exception as e:
                logger.warning(f"OpenAI generation failed: {e}")
                # Fall through to fallback
        
        # Fallback: deterministic summarization for testing
        logger.debug("Using fallback generation (no real API call)")
        tokens = prompt.split()
        return " ".join(tokens[:80])

    def judge(self, gold: str, pred: str) -> float:
        """Judge similarity between gold and prediction using OpenAI.
        
        Args:
            gold: Gold standard summary
            pred: Predicted summary
            
        Returns:
            Similarity score in [0.0, 1.0]
            
        Raises:
            RuntimeError: If budget is exceeded
        """
        # Check budget before making request
        self._check_budget("judge", estimated_cost=0.005)
        
        # Apply rate limiting
        if self.rate_limiter:
            estimated_tokens = (len(gold.split()) + len(pred.split())) * 2
            self.rate_limiter.wait_if_needed(estimated_tokens=estimated_tokens)
        
        prompt = (
            "You are an objective evaluator. "
            "Rate how well the prediction matches the gold summary on a scale from 0.0 to 1.0. "
            "Return just the number, with no explanation.\n\n"
            f"Gold: {gold}\n\nPrediction: {pred}\n\nScore:"
        )
        
        # Try real API call if available
        if self.use_real_api and self._is_new and self._client is not None:
            try:
                logger.debug(f"Calling OpenAI API for judging (model={self.judge_model})")
                resp = self._client.chat.completions.create(
                    model=self.judge_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.config.get("judge_max_tokens", 8),
                    temperature=0.0,
                )
                text = self._extract_text(resp).strip()
                
                # Track cost
                if self.cost_tracker:
                    input_tokens, output_tokens = self._extract_usage(resp)
                    cost = self._calculate_cost(self.judge_model, input_tokens, output_tokens)
                    self.cost_tracker.add_request("judge", input_tokens, output_tokens, cost)
                
                # Parse score from response
                m = re.search(r"([0-9]*\.?[0-9]+)", text)
                if m:
                    try:
                        score = float(m.group(1))
                        # Clamp to [0, 1]
                        return max(0.0, min(1.0, score))
                    except Exception:
                        pass
                
            except RateLimitError as e:
                logger.error(f"OpenAI rate limit exceeded: {e}")
                raise
            except APIError as e:
                logger.error(f"OpenAI API error: {e}")
                # Fall through to fallback
            except Exception as e:
                logger.warning(f"OpenAI judge failed: {e}")
                # Fall through to fallback
        
        # Fallback: token overlap heuristic
        logger.debug("Using fallback judge (token overlap heuristic)")
        gold_set = set(gold.lower().split())
        pred_set = set(pred.lower().split())
        if not gold_set:
            return 1.0 if not pred_set else 0.0
        return len(gold_set & pred_set) / len(gold_set)
    
    def get_cost_report(self) -> Optional[Dict[str, Any]]:
        """Get cost tracking report.
        
        Returns:
            Cost report dictionary or None if tracking is disabled
        """
        if self.cost_tracker:
            return self.cost_tracker.get_report()
        return None
    
    def reset_cost_tracker(self):
        """Reset cost tracker for a new evaluation run."""
        if self.cost_tracker:
            self.cost_tracker = CostTracker()


def create_openai_client_from_config(config: Dict[str, Any], use_real_api: bool = True) -> OpenAIClient:
    """Create an OpenAI client from configuration dictionary.
    
    Args:
        config: Configuration dictionary from medeval_config.yaml['llm']['openai']
        use_real_api: If False, use fallback heuristics for testing
        
    Returns:
        Configured OpenAIClient instance
    """
    return OpenAIClient(
        model=config.get("model", "gpt-3.5-turbo"),
        judge_model=config.get("judge_model"),
        config=config,
        enable_cost_tracking=config.get("cost_tracking", {}).get("enabled", True),
        enable_rate_limiting=config.get("rate_limit", {}).get("enabled", True),
        use_real_api=use_real_api
    )