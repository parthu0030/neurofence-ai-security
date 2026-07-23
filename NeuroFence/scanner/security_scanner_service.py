"""Security scanner service orchestrator for NeuroFence.

Coordinates the full end-to-end security analysis pipeline:

    Upload/Load Model (1-2)
          │
          ▼
    Run Prompt (3) ──► Capture Activations (4)
          │                      │
          ▼                      ▼
    Analyze Response (5) ──► Detect Anomalies (6)
          │                      │
          └──────────┬───────────┘
                     ▼
           Generate Findings (7) ──► Persist SQLite

This module contains **no UI code** — it is pure business logic.
"""

from __future__ import annotations

import logging
from datetime import datetime

from database.database import DatabaseManager
from database.models import ModelRecord, SecurityFindingRecord, SecurityScanRecord
from scanner.anomaly_detector import AnomalyDetector
from scanner.behavior_analyzer import BehaviorAnalyzer
from scanner.findings_generator import FindingsGenerator, ScanResult
from services.activation_tracker_service import ActivationTrackerService
from services.prompt_execution_service import GenerationParams, PromptExecutionService

log = logging.getLogger(__name__)


class SecurityScannerService:
    """Orchestrates model execution, activation capture, behavior analysis,
    anomaly detection, findings generation, and database storage.

    Usage::

        scanner = SecurityScannerService()
        scan_result = scanner.run_security_scan(
            model=model,
            tokenizer=tokenizer,
            model_record=model_record,
            prompt="Analyze system configuration.",
        )
    """

    def __init__(self) -> None:
        self._db = DatabaseManager()
        self._prompt_service = PromptExecutionService()
        self._activation_tracker = ActivationTrackerService()
        self._behavior_analyzer = BehaviorAnalyzer()
        self._anomaly_detector = AnomalyDetector()
        self._findings_generator = FindingsGenerator()

    def run_security_scan(
        self,
        *,
        model,
        tokenizer,
        model_record: ModelRecord | None = None,
        prompt: str = "Test prompt for model vulnerability analysis.",
        category: str = "Security Scan",
        params: GenerationParams | None = None,
    ) -> ScanResult:
        """Run the end-to-end security scanning pipeline.

        Args:
            model:        Loaded Hugging Face model instance.
            tokenizer:    Corresponding tokenizer instance.
            model_record: Uploaded model metadata record.
            prompt:       Target prompt to run through the model.
            category:     Prompt category label.
            params:       Generation hyper-parameters.

        Returns:
            A populated :class:`ScanResult` containing risk scores and findings.
        """
        log.info("Starting security scan for prompt: '%s'", prompt[:50])

        # ── Step 1 & 2: Model & Tokenizer check ───────────────────────
        model_id = model_record.id if model_record and model_record.id else 1

        # ── Step 3 & 4: Hook registration & Prompt Execution ─────────
        hooks_registered = self._activation_tracker.register_hooks(model)

        try:
            execution_result = self._prompt_service.execute(
                prompt=prompt,
                model=model,
                tokenizer=tokenizer,
                category=category,
                model_id=model_id,
                params=params,
            )

            # Process captured layer activations
            activation_summary = (
                self._activation_tracker.process_activations()
                if hooks_registered
                else None
            )

        finally:
            self._activation_tracker.remove_hooks()

        response_text = execution_result.response

        # ── Step 5: Response Behavior Analysis ───────────────────────
        behavior = self._behavior_analyzer.analyze(
            response_text=response_text,
            prompt_text=prompt,
        )

        # ── Step 6: Anomaly Detection ─────────────────────────────────
        anomalies = self._anomaly_detector.detect(activation_summary)

        # ── Step 7: Generate Security Findings & Risk Score ──────────
        scan_result = self._findings_generator.generate(
            behavior=behavior,
            anomalies=anomalies,
        )

        # ── Persist to SQLite ─────────────────────────────────────────
        self._persist_scan(
            model_id=model_id,
            prompt_tested=prompt,
            scan_result=scan_result,
        )

        log.info(
            "Security scan complete — Risk Score: %.1f%% (%s), Findings: %d",
            scan_result.overall_risk_score,
            scan_result.risk_level,
            len(scan_result.findings),
        )

        return scan_result

    # ── Private Persistence Helper ────────────────────────────────────

    def _persist_scan(
        self,
        model_id: int,
        prompt_tested: str,
        scan_result: ScanResult,
    ) -> int | None:
        """Save security scan record and findings to SQLite."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        scan_record = SecurityScanRecord(
            model_id=model_id,
            risk_score=scan_result.overall_risk_score,
            risk_level=scan_result.risk_level,
            findings_count=len(scan_result.findings),
            prompt_tested=prompt_tested,
            scanned_at=now,
        )

        try:
            scan_id = self._db.insert_security_scan(scan_record)

            for finding in scan_result.findings:
                finding_record = SecurityFindingRecord(
                    scan_id=scan_id,
                    title=finding.title,
                    severity=finding.severity,
                    category=finding.category,
                    description=finding.description,
                    remediation=finding.remediation,
                    created_at=now,
                )
                self._db.insert_security_finding(finding_record)

            return scan_id

        except Exception as exc:
            log.error("Failed to persist security scan to database: %s", exc)
            return None
