"""Request failures must not hide programming errors (#73)."""
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from oss_contribution_finder import api_request


@pytest.mark.parametrize("error_type", [AttributeError, TypeError, KeyError])
def test_unexpected_errors_propagate_without_retry(error_type):
    error = error_type("synthetic programming failure")
    with patch("urllib.request.urlopen", side_effect=error) as request, \
            patch("time.sleep") as sleep:
        with pytest.raises(error_type) as caught:
            api_request("https://example.invalid", retries=3, use_cache=False)
    assert caught.value is error
    assert request.call_count == 1
    sleep.assert_not_called()


@pytest.mark.parametrize("error", [
    urllib.error.URLError("synthetic network failure"),
    TimeoutError("synthetic timeout"),
    json.JSONDecodeError("synthetic invalid JSON", "x", 0),
])
def test_expected_errors_retain_retry_and_error_response(error):
    with patch("urllib.request.urlopen", side_effect=error) as request, \
            patch("time.sleep") as sleep:
        result = api_request("https://example.invalid", retries=2, use_cache=False)
    assert result == {"error": str(error)}
    assert request.call_count == 2
    sleep.assert_called_once_with(1.0)


def test_network_retry_can_recover():
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b'{"ok": true}'
    with patch("urllib.request.urlopen", side_effect=[urllib.error.URLError("offline"), response]), \
            patch("time.sleep") as sleep:
        result = api_request("https://example.invalid", retries=2, use_cache=False)
    assert result == {"ok": True}
    sleep.assert_called_once_with(1.0)
