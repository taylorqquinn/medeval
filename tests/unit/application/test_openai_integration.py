"""Test OpenAI client components without making real API calls."""

from medeval.application.openai_client import OpenAIClient, CostTracker, RateLimiter
import time

def test_cost_tracker():
    """Test cost tracking functionality."""
    print('=== Testing Cost Tracker ===')
    tracker = CostTracker()
    tracker.add_request('generate', 100, 50, 0.001)
    tracker.add_request('judge', 20, 5, 0.0001)
    report = tracker.get_report()
    print(f'Total cost: ${report["total_cost_usd"]:.6f}')
    print(f'Total requests: {report["total_requests"]}')
    print(f'Cost by operation: {report["cost_by_operation"]}')
    assert report["total_cost_usd"] == 0.0011
    assert report["total_requests"] == 2
    print('[OK] Cost tracker passed')

def test_rate_limiter():
    """Test rate limiting functionality."""
    print('\n=== Testing Rate Limiter ===')
    limiter = RateLimiter(max_requests_per_minute=5, min_delay_seconds=0.1)
    start = time.time()
    for i in range(3):
        limiter.wait_if_needed(estimated_tokens=100)
        print(f'Request {i+1} allowed')
    elapsed = time.time() - start
    print(f'Elapsed: {elapsed:.2f}s (expected ~0.2s for 2 delays)')
    assert elapsed >= 0.2, f"Expected at least 0.2s delay, got {elapsed:.2f}s"
    print('[OK] Rate limiter passed')

def test_openai_client():
    """Test OpenAI client in test mode."""
    print('\n=== Testing OpenAI Client (Test Mode) ===')
    client = OpenAIClient(use_real_api=False, enable_cost_tracking=True)
    
    # Test generation
    summary = client.generate('Patient has chest pain and shortness of breath')
    print(f'Generated: {summary[:50]}...')
    assert len(summary) > 0
    
    # Test judge
    score = client.judge('Gold summary text', 'Predicted summary text')
    print(f'Judge score: {score:.3f}')
    assert 0.0 <= score <= 1.0
    
    # Test cost report (should be None since no real API calls)
    report = client.get_cost_report()
    print(f'Cost report: {report}')
    assert report["total_requests"] == 0  # No real API calls in test mode
    
    print('[OK] OpenAI client passed')

if __name__ == '__main__':
    test_cost_tracker()
    test_rate_limiter()
    test_openai_client()
    print('\n[OK] All tests passed!')

