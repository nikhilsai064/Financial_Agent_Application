"""Runtime configuration, resolved from environment variables."""

from __future__ import annotations

import os

# Default model used by every agent unless a caller overrides it. Claude Opus
# 4.8 per Anthropic's current guidance for agentic, reasoning-heavy work.
DEFAULT_MODEL = os.environ.get("FINANCIAL_AGENT_MODEL", "claude-opus-4-8")

# Safety cap on how many tool-use round trips a single agent may take.
MAX_TOOL_ITERATIONS = int(os.environ.get("FINANCIAL_AGENT_MAX_ITERATIONS", "8"))
