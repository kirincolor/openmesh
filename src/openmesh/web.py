"""Compatibility alias. The app lives in openmesh.server."""

from .server import create_app

__all__ = ["create_app"]
