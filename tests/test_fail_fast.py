import pytest
from reqflow.core.adapters.api import APIAdapter


def test_api_adapter_raises_on_http_error():
    """API adapter must raise RuntimeError on HTTP errors, not return error response."""
    adapter = APIAdapter(
        api_key="invalid-key",
        base_url="https://httpbin.org",
        model="gpt-4o",
        provider="openai",
    )
    with pytest.raises(RuntimeError, match="API call failed"):
        adapter.call(prompt="test")
