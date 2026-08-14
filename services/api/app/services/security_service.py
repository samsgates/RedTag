from sqlalchemy.orm import Session

from app.agents.security import inspect_untrusted_text
from app.core.config import get_settings
from app.models.domain import SecurityEvent
from app.services.audit import audit


def _record(
    db: Session,
    *,
    tenant_id: str,
    incident_id: str | None,
    source: str,
    category: str,
    severity: str,
    details: dict,
) -> SecurityEvent:
    row = SecurityEvent(
        tenant_id=tenant_id,
        incident_id=incident_id,
        category=category,
        severity=severity,
        source=source,
        attempted_action="untrusted_instruction",
        decision="BLOCKED",
        details=details,
    )
    db.add(row)
    audit(
        db,
        tenant_id=tenant_id,
        incident_id=incident_id,
        actor_type="system",
        actor_id="security-layer",
        event_type="security.policy_blocked",
        payload={"category": category, "source": source},
    )
    return row


def inspect_text_and_record(
    db: Session,
    *,
    tenant_id: str,
    incident_id: str | None,
    source: str,
    text: str,
) -> list[SecurityEvent]:
    rows: list[SecurityEvent] = []
    for matched in inspect_untrusted_text(text):
        rows.append(
            _record(
                db,
                tenant_id=tenant_id,
                incident_id=incident_id,
                source=source,
                category="PROMPT_INJECTION",
                severity="HIGH",
                details={"detector": "baseline", "matched_pattern": matched},
            )
        )

    settings = get_settings()
    if settings.model_armor_enabled:
        try:
            from app.services.model_armor import ModelArmorGuard

            result = ModelArmorGuard().inspect_text(text)
            if result.blocked:
                rows.append(
                    _record(
                        db,
                        tenant_id=tenant_id,
                        incident_id=incident_id,
                        source=source,
                        category="MODEL_ARMOR_BLOCK",
                        severity="HIGH",
                        details={
                            "detector": "google-model-armor",
                            "match_state": result.match_state,
                            "invocation_result": result.invocation_result,
                            "filters": list(result.filters),
                        },
                    )
                )
        except Exception as exc:
            if settings.model_armor_fail_closed:
                rows.append(
                    _record(
                        db,
                        tenant_id=tenant_id,
                        incident_id=incident_id,
                        source=source,
                        category="MODEL_ARMOR_UNAVAILABLE",
                        severity="HIGH",
                        details={"detector": "google-model-armor", "error_type": type(exc).__name__},
                    )
                )
    return rows


def inspect_binary_and_record(
    db: Session,
    *,
    tenant_id: str,
    incident_id: str | None,
    source: str,
    content: bytes,
    byte_type: str,
) -> list[SecurityEvent]:
    settings = get_settings()
    if not settings.model_armor_enabled:
        return []
    try:
        from app.services.model_armor import ModelArmorGuard

        result = ModelArmorGuard().inspect_bytes(content, byte_type)
        if not result.blocked:
            return []
        return [
            _record(
                db,
                tenant_id=tenant_id,
                incident_id=incident_id,
                source=source,
                category="MODEL_ARMOR_BLOCK",
                severity="HIGH",
                details={
                    "detector": "google-model-armor",
                    "byte_type": byte_type,
                    "match_state": result.match_state,
                    "invocation_result": result.invocation_result,
                    "filters": list(result.filters),
                },
            )
        ]
    except Exception as exc:
        if not settings.model_armor_fail_closed:
            return []
        return [
            _record(
                db,
                tenant_id=tenant_id,
                incident_id=incident_id,
                source=source,
                category="MODEL_ARMOR_UNAVAILABLE",
                severity="HIGH",
                details={
                    "detector": "google-model-armor",
                    "byte_type": byte_type,
                    "error_type": type(exc).__name__,
                },
            )
        ]


def inspect_pdf_and_record(
    db: Session,
    *,
    tenant_id: str,
    incident_id: str | None,
    source: str,
    content: bytes,
) -> list[SecurityEvent]:
    return inspect_binary_and_record(
        db,
        tenant_id=tenant_id,
        incident_id=incident_id,
        source=source,
        content=content,
        byte_type="PDF",
    )
