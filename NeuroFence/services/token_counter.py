"""Token counting utilities for NeuroFence Prompt Engine.

Provides helper functions for counting tokens and computing
inference statistics.  Keeps this logic out of the service layer
so it can be reused and tested independently.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class TokenCounter:
    """Stateless utility for token-counting and statistics."""

    @staticmethod
    def count_tokens(text: str, tokenizer) -> int:
        """Tokenize *text* and return the number of tokens.

        Args:
            text: The string to tokenize.
            tokenizer: A HuggingFace ``PreTrainedTokenizer`` instance.

        Returns:
            Token count as an ``int``.
        """
        try:
            return len(tokenizer.encode(text, add_special_tokens=True))
        except Exception as exc:
            log.warning("Token counting failed: %s — returning 0.", exc)
            return 0

    @staticmethod
    def compute_statistics(
        input_tokens: int,
        output_tokens: int,
        inference_time: float,
    ) -> dict[str, float]:
        """Compute derived statistics from raw inference data.

        Returns:
            A dict with keys ``"characters_generated"`` (not available
            here — computed by caller) and ``"avg_tokens_per_second"``.
        """
        avg_tps = output_tokens / inference_time if inference_time > 0 else 0.0
        return {
            "avg_tokens_per_second": round(avg_tps, 2),
        }
