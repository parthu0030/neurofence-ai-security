"""Prompt execution service for NeuroFence.

Orchestrates the prompt → tokenize → generate → decode pipeline.
Returns a :class:`PromptExecutionResult` with all statistics.

This module contains **no UI code** — it is pure business logic.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime

import torch

from database.models import PromptExecutionResult
from services.token_counter import TokenCounter

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class GenerationParams:
    """User-configurable generation hyper-parameters.

    Attributes:
        temperature:    Sampling temperature (0.0 – 2.0).
        top_p:          Nucleus sampling probability (0.0 – 1.0).
        top_k:          Top-k filtering (0 – 100).
        max_new_tokens: Maximum number of tokens to generate (16 – 512).
    """

    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    max_new_tokens: int = 128


class PromptExecutionError(Exception):
    """Raised when prompt execution fails in a recoverable way."""


class PromptExecutionService:
    """Tokenizes a prompt, generates a response, and returns statistics.

    Usage::

        service = PromptExecutionService()
        result = service.execute(
            prompt="Hello, who are you?",
            model=model,
            tokenizer=tokenizer,
            category="Normal",
            params=GenerationParams(),
        )
    """

    def __init__(self) -> None:
        self._counter = TokenCounter()

    # ── Public API ───────────────────────────────────────────────────

    def execute(
        self,
        *,
        prompt: str,
        model,
        tokenizer,
        category: str = "Custom",
        model_id: int = 0,
        params: GenerationParams | None = None,
    ) -> PromptExecutionResult:
        """Run inference and return a structured result.

        All exceptions are caught and wrapped into a failed
        ``PromptExecutionResult`` so the UI can display a friendly
        error message.

        Args:
            prompt:    The user's input prompt.
            model:     A loaded ``AutoModelForCausalLM`` instance.
            tokenizer: The corresponding ``AutoTokenizer``.
            category:  Prompt category label for the history table.
            model_id:  Foreign key for ``uploaded_models.id``.
            params:    Generation hyper-parameters.

        Returns:
            A :class:`PromptExecutionResult` with status ``"success"``
            or ``"error"``.
        """
        if params is None:
            params = GenerationParams()

        # ── Validation ────────────────────────────────────────────────
        if not prompt or not prompt.strip():
            return self._error_result(
                prompt=prompt,
                category=category,
                message="Prompt is empty. Please enter a prompt before running.",
            )

        if model is None:
            return self._error_result(
                prompt=prompt,
                category=category,
                message="No model is loaded. Please upload and load a model first.",
            )

        if tokenizer is None:
            return self._error_result(
                prompt=prompt,
                category=category,
                message="Tokenizer is not available. The model may have been loaded without a tokenizer.",
            )

        # ── Execution ────────────────────────────────────────────────
        try:
            return self._run_inference(
                prompt=prompt,
                model=model,
                tokenizer=tokenizer,
                category=category,
                params=params,
            )
        except torch.cuda.OutOfMemoryError:
            return self._error_result(
                prompt=prompt,
                category=category,
                message=(
                    "GPU out of memory. Try reducing Max Tokens or "
                    "use a smaller model."
                ),
            )
        except MemoryError:
            return self._error_result(
                prompt=prompt,
                category=category,
                message=(
                    "System ran out of memory during generation. "
                    "Try reducing Max Tokens or close other applications."
                ),
            )
        except Exception as exc:
            log.exception("Prompt execution failed.")
            return self._error_result(
                prompt=prompt,
                category=category,
                message=f"Generation failed: {exc}",
            )

    # ── Private helpers ──────────────────────────────────────────────

    def _run_inference(
        self,
        *,
        prompt: str,
        model,
        tokenizer,
        category: str,
        params: GenerationParams,
    ) -> PromptExecutionResult:
        """Core inference pipeline — no exception handling here."""
        device = next(model.parameters()).device

        # Tokenize
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        ).to(device)

        input_token_count = inputs["input_ids"].shape[1]

        # Generate
        log.info(
            "Generating with temp=%.2f, top_p=%.2f, top_k=%d, max_new_tokens=%d",
            params.temperature,
            params.top_p,
            params.top_k,
            params.max_new_tokens,
        )

        # Build generation kwargs — temperature=0 means greedy
        gen_kwargs: dict = {
            "max_new_tokens": params.max_new_tokens,
            "pad_token_id": tokenizer.eos_token_id or tokenizer.pad_token_id or 0,
        }

        if params.temperature > 0:
            gen_kwargs["do_sample"] = True
            gen_kwargs["temperature"] = params.temperature
            gen_kwargs["top_p"] = params.top_p
            gen_kwargs["top_k"] = params.top_k
        else:
            gen_kwargs["do_sample"] = False

        start = time.perf_counter()

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                **gen_kwargs,
            )

        elapsed = time.perf_counter() - start

        # Decode — strip the input tokens from the output
        generated_ids = output_ids[0][input_token_count:]
        response_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

        output_token_count = len(generated_ids)
        characters = len(response_text)
        avg_tps = (
            round(output_token_count / elapsed, 2) if elapsed > 0 else 0.0
        )

        log.info(
            "Generation complete — %d tokens in %.2fs (%.1f tok/s)",
            output_token_count,
            elapsed,
            avg_tps,
        )

        return PromptExecutionResult(
            prompt=prompt,
            response=response_text,
            category=category,
            input_tokens=input_token_count,
            output_tokens=output_token_count,
            characters_generated=characters,
            inference_time=round(elapsed, 4),
            avg_tokens_per_second=avg_tps,
            status="success",
            error_message="",
        )

    @staticmethod
    def _error_result(
        *,
        prompt: str,
        category: str,
        message: str,
    ) -> PromptExecutionResult:
        """Build a failed ``PromptExecutionResult``."""
        return PromptExecutionResult(
            prompt=prompt,
            response="",
            category=category,
            input_tokens=0,
            output_tokens=0,
            characters_generated=0,
            inference_time=0.0,
            avg_tokens_per_second=0.0,
            status="error",
            error_message=message,
        )
