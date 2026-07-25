import pytest

from connectors.http.fetcher import FetchError, ProductFetcher


def test_invalid_url():
    with ProductFetcher(timeout=5) as fetcher:
        with pytest.raises(FetchError):
            fetcher.fetch("https://this-domain-does-not-exist-123456.com")
