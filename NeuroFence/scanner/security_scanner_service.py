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

import time
from database.database import DatabaseManager
from database.models import ModelRecord, SecurityFindingRecord, SecurityScanRecord
from scanner.anomaly_detector import AnomalyDetector
from scanner.behavior_analyzer import BehaviorAnalyzer
from scanner.findings_generator import FindingsGenerator, ScanResult
from services.activation_tracker_service import ActivationTrackerService
from services.prompt_execution_service import GenerationParams, PromptExecutionService
from services.scan_history_service import ScanHistoryService

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
        self._history_service = ScanHistoryService(self._db)

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
        start_time = time.time()

        # ── Step 1 & 2: Model & Tokenizer check ───────────────────────
        model_id = model_record.id if model_record and model_record.id else 1
        sha256_fp = model_record.sha256 if model_record and model_record.sha256 else ""

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

        elapsed_time = round(time.time() - start_time, 3)

        # Extract activation stats
        avg_act = getattr(activation_summary, "average_activation", 0.0) if activation_summary else 0.0
        peak_act = getattr(activation_summary, "peak_activation", 0.0) if activation_summary else 0.0

        # ── Persist to SQLite ─────────────────────────────────────────
        self._persist_scan(
            model_id=model_id,
            prompt_tested=prompt,
            scan_result=scan_result,
            execution_time=elapsed_time,
            average_activation=avg_act,
            peak_activation=peak_act,
            sha256=sha256_fp,
        )

        log.info(
            "Security scan complete — Risk Score: %.1f%% (%s), Findings: %d, Time: %.3fs",
            scan_result.overall_risk_score,
            scan_result.risk_level,
            len(scan_result.findings),
            elapsed_time,
        )

        return scan_result

    # ── Private Persistence Helper ────────────────────────────────────

    def _persist_scan(
        self,
        model_id: int,
        prompt_tested: str,
        scan_result: ScanResult,
        execution_time: float = 0.0,
        average_activation: float = 0.0,
        peak_activation: float = 0.0,
        sha256: str = "",
    ) -> int | None:
        """Save security scan record, findings, and summary to SQLite."""
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

            critical_c = 0
            high_c = 0
            med_c = 0
            low_c = 0

            for finding in scan_result.findings:
                sev = str(finding.severity).lower()
                if "critical" in sev:
                    critical_c += 1
                elif "high" in sev:
                    high_c += 1
                elif "med" in sev:
                    med_c += 1
                else:
                    low_c += 1

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

            # Calculate Security Score (100 - risk_score)
            sec_score = max(0.0, min(100.0, 100.0 - scan_result.overall_risk_score))
            overall_status = f"{scan_result.risk_level} Risk" if scan_result.risk_level != "Clean" else "Clean"

            # Store in scan_summary table
            self._history_service.store_scan(
                model_id=model_id,
                scan_date=now,
                security_score=sec_score,
                overall_status=overall_status,
                critical_count=critical_c,
                high_count=high_c,
                medium_count=med_c,
                low_count=low_c,
                average_activation=average_activation,
                peak_activation=peak_activation,
                execution_time=execution_time,
                sha256=sha256,
            )

            return scan_id

        except Exception as exc:
            log.error("Failed to persist security scan to database: %s", exc)
            return None

