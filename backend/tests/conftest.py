"""Test configuration. Forces offline mode so the whole suite runs with no
credentials and no network."""

from __future__ import annotations

import os

os.environ.setdefault("MODEL_PROVIDER", "local")
os.environ.setdefault("KNOWLEDGE_BACKEND", "graphrag")
os.environ.setdefault("ENABLE_CONTENT_SAFETY", "false")
