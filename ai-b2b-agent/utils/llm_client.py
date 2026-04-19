"""
LLM client helper
=================
Provides a safe Anthropic client initializer.
"""

import os
import anthropic
from utils.logger import setup_logger

logger = setup_logger("llm_client")


def get_anthropic_client():
    """Return an Anthropic client if key exists, else None.

    This prevents the SDK from throwing auth resolution errors when
    no credentials are configured in local demo runs.
    """
    api_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set. Falling back to local demo logic.")
        return None
    return anthropic.Anthropic(api_key=api_key)
