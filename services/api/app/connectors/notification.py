import smtplib
from email.message import EmailMessage
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.base import Connector, ConnectorResult
from app.core.config import get_settings
from app.models.domain import Customer, Notification


class NotificationConnector(Connector):
    name = "notification"

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.settings = get_settings()

    def health(self) -> dict:
        if not self.settings.real_notifications_enabled:
            return {"status": "ok", "mode": "mock"}
        if self.settings.smtp_host or self.settings.notification_webhook_url:
            return {"status": "ok", "mode": "configured"}
        return {"status": "degraded", "reason": "No real notification provider configured"}

    def _customer(self, customer_id: str) -> Customer | None:
        return self.db.scalar(
            select(Customer).where(
                Customer.tenant_id == self.tenant_id,
                Customer.id == customer_id,
            )
        )

    def _notification(self, incident_id: str, customer_id: str, channel: str) -> Notification | None:
        return self.db.scalar(
            select(Notification).where(
                Notification.tenant_id == self.tenant_id,
                Notification.incident_id == incident_id,
                Notification.customer_id == customer_id,
                Notification.channel == channel,
            )
        )

    def _send_email(self, customer: Customer, subject: str, body: str) -> str:
        if not customer.email:
            raise ValueError("Customer has no email")
        if not self.settings.smtp_host:
            raise RuntimeError("SMTP_HOST is not configured")
        message = EmailMessage()
        message["From"] = self.settings.smtp_from
        message["To"] = customer.email
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            if self.settings.smtp_user:
                smtp.login(self.settings.smtp_user, self.settings.smtp_password or "")
            smtp.send_message(message)
        return f"smtp:{uuid4().hex}"

    def _send_webhook(self, customer: Customer, channel: str, body: str) -> str:
        if not self.settings.notification_webhook_url:
            raise RuntimeError("NOTIFICATION_WEBHOOK_URL is not configured")
        response = httpx.post(
            self.settings.notification_webhook_url,
            json={
                "customer_ref": customer.external_ref,
                "channel": channel,
                "phone": customer.phone if channel == "sms" else None,
                "email": customer.email if channel == "email" else None,
                "message": body,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.headers.get("x-provider-id") or f"webhook:{uuid4().hex}"

    def execute(self, action: str, target_id: str, payload: dict) -> ConnectorResult:
        customer = self._customer(target_id)
        if not customer:
            return ConnectorResult(False, None, None, None, "Customer not found")
        incident_id = str(payload.get("incident_id", ""))
        if not incident_id:
            return ConnectorResult(False, None, None, None, "incident_id is required")
        channel = "email" if action == "customer.notify_email" else "sms" if action == "customer.notify_sms" else ""
        if not channel:
            return ConnectorResult(False, None, None, None, f"Unsupported action: {action}")

        row = self._notification(incident_id, customer.id, channel)
        if not row:
            row = Notification(
                tenant_id=self.tenant_id,
                incident_id=incident_id,
                customer_id=customer.id,
                channel=channel,
                template_id=str(payload.get("template_id", "recall-safety-v1")),
            )
            self.db.add(row)
            self.db.flush()

        before = {"status": row.status, "attempt_count": row.attempt_count}
        if row.status == "DELIVERED":
            return ConnectorResult(True, row.provider_ref, before, before)
        row.attempt_count += 1

        subject = str(payload.get("subject", "Important product safety recall"))
        body = str(payload.get("message", "A product you purchased is subject to a safety recall."))
        try:
            if not self.settings.real_notifications_enabled:
                if channel == "email" and (not customer.email or "fail" in customer.email):
                    raise ValueError("Simulated email delivery failure")
                if channel == "sms" and not customer.phone:
                    raise ValueError("Customer has no phone")
                provider_ref = f"mock:{channel}:{uuid4().hex}"
            elif channel == "email" and self.settings.smtp_host:
                provider_ref = self._send_email(customer, subject, body)
            else:
                provider_ref = self._send_webhook(customer, channel, body)
            row.status = "DELIVERED"
            row.provider_ref = provider_ref
            row.error = None
            self.db.flush()
            after = {"status": row.status, "attempt_count": row.attempt_count, "provider_ref": provider_ref}
            return ConnectorResult(True, provider_ref, before, after)
        except Exception as exc:
            row.status = "FAILED"
            row.error = str(exc)
            self.db.flush()
            after = {"status": row.status, "attempt_count": row.attempt_count, "error": row.error}
            return ConnectorResult(False, None, before, after, row.error)

    def verify(self, action: str, target_id: str, expected: dict) -> dict:
        incident_id = str(expected.get("incident_id", ""))
        channel = "email" if action == "customer.notify_email" else "sms"
        row = self._notification(incident_id, target_id, channel)
        if not row:
            return {"verified": False, "reason": "Notification record not found"}
        return {
            "verified": row.status == expected.get("status", "DELIVERED"),
            "actual": {"status": row.status, "provider_ref": row.provider_ref},
            "expected": expected,
        }
