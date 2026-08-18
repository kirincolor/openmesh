from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urljoin, urlparse


def blocked_reason(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return "only http(s) URLs"
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return "missing host"
    if host in {"localhost", "127.0.0.1", "::1", "0.0.0.0", "[::1]"}:
        return "blocked local host"
    if host.endswith(".local") or host.endswith(".internal"):
        return "blocked internal host"
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return "cannot resolve host"
    for info in infos:
        raw = info[4][0]
        try:
            ip = ipaddress.ip_address(raw)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return f"blocked address {ip}"
    return None


def next_url(current: str, location: str) -> str:
    return urljoin(current, location)
