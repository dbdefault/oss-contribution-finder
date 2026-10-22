"""Regression: --sort friendliness must not send sort=friendliness to GitHub (#78).

GitHub Search Issues only accepts comments, reactions, created, and updated.
Passing friendliness makes the API ignore the sort parameter. Local ranking by
friendliness_score still runs, but only on the default-ordered page. The API
call must use a valid sort (updated) while the CLI keeps local friendliness
ordering.
"""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import oss_contribution_finder as ocf

VALID_API_SORTS = {"comments", "reactions", "created", "updated"}


def _sort_passed_to_search(argv):
    captured = {}

    def fake_search_issues(**kwargs):
        captured.update(kwargs)
        return {"total_count": 0, "items": []}

    with patch.object(sys, "argv", ["oss-contribution-finder", "--no-cache"] + argv), \
            patch.object(ocf, "search_issues", fake_search_issues), \
            patch.object(ocf, "get_token", lambda: "test_token"):
        ocf.main()
    return captured["sort"]


def test_friendliness_maps_to_valid_api_sort():
    """--sort friendliness must forward a GitHub-valid sort, not 'friendliness'."""
    api_sort = _sort_passed_to_search(["--sort", "friendliness"])
    assert api_sort != "friendliness"
    assert api_sort in VALID_API_SORTS


def test_native_sorts_still_forwarded():
    """Native API sort choices continue to pass through unchanged."""
    for value in ("comments", "reactions", "updated"):
        assert _sort_passed_to_search(["--sort", value]) == value
