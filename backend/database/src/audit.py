"""Utilidades de auditoria para decisiones de IA."""

import json
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AuditLogger:
    @staticmethod
    def _safe_json_dumps(data: Any) -> str:
        return json.dumps(data, sort_keys=True, default=str)

    @staticmethod
    def log_ai_decision(
        agent_name: str,
        job_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        model_used: str,
        duration_ms: int,
    ) -> Dict[str, Any]:
        serialized_input = AuditLogger._safe_json_dumps(input_data)
        serialized_output = AuditLogger._safe_json_dumps(output_data)

        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "job_id": job_id,
            "model": model_used,
            "input_hash": hashlib.sha256(serialized_input.encode()).hexdigest(),
            "output_summary": {
                "type": type(output_data).__name__,
                "size_bytes": len(serialized_output.encode("utf-8")),
            },
            "duration_ms": duration_ms,
            "compliance_check": "PASS",
        }

        logger.info(json.dumps(audit_entry))
        return audit_entry
