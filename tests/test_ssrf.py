from openmesh.ssrf import blocked_reason


def test_blocks_localhost() -> None:
    assert blocked_reason("http://127.0.0.1/secret")
    assert blocked_reason("http://localhost:8787/api/secrets")


def test_blocks_file() -> None:
    assert blocked_reason("file:///etc/passwd")


def test_allows_public_https() -> None:
    assert blocked_reason("https://example.com/page") is None
