"""Application package bootstrap and public API.

Responsibilities:
- Load environment variables from a local .env at import time for local development.
- Provide organized modules for graphs, models, state, tools, and a simple RAG utility.
- Expose key submodules via __all__ for convenient imports.
"""
from __future__ import annotations

# Load environment variables from a .env file at import time so local servers pick them up
try:
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(), override=False)
except Exception:
    # dotenv not installed or .env not found; continue silently
    pass

__all__ = ["graphs", "models", "state", "tools", "rag"]

