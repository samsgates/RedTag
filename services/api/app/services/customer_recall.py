from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Action, Customer, Incident, Notification, Order, ReturnCase
from app.services.actions import execute_action, request_action, verify_action
from app.services.audit import audit
from app.services.workflow import RecallWorkflow


class CustomerRecallService:
    def __init__(self, db: Session):
        self.db = db

    def _affected_orders(self, incident: Incident) -> list[Order]:
        batches = RecallWorkflow(self.db)._approved_batches(incident)
        if not batches:
            return []
        return list(
            self.db.scalars(
                select(Order).where(
                    Order.tenant_id == incident.tenant_id,
                    Order.manufacturing_batch_id.in_(batches),
                )
            )
        )

    def notify(self, incident: Incident) -> list[Action]:
        actions: list[Action] = []
        for order in self._affected_orders(incident):
            customer = self.db.scalar(
                select(Customer).where(
                    Customer.tenant_id == incident.tenant_id,
                    Customer.id == order.customer_id,
                )
            )
            if not customer or not customer.contact_allowed:
                continue

            already_delivered = bool(
                self.db.scalar(
                    select(Notification.id).where(
                        Notification.tenant_id == incident.tenant_id,
                        Notification.incident_id == incident.id,
                        Notification.customer_id == customer.id,
                        Notification.status == "DELIVERED",
                    )
                )
            )
            if already_delivered:
                existing_return = self.db.scalar(
                    select(ReturnCase).where(
                        ReturnCase.tenant_id == incident.tenant_id,
                        ReturnCase.incident_id == incident.id,
                        ReturnCase.order_id == order.id,
                    )
                )
                if not existing_return:
                    self.db.add(
                        ReturnCase(
                            tenant_id=incident.tenant_id,
                            incident_id=incident.id,
                            customer_id=customer.id,
                            order_id=order.id,
                            status="OPEN",
                        )
                    )
                continue

            base_payload = {
                "incident_id": incident.id,
                "template_id": "recall-safety-v1",
                "subject": f"Important safety notice for {order.product_id}",
                "message": (
                    f"Hello {customer.first_name}. A product associated with order {order.id} is "
                    "included in a safety recall. Please stop using the product and follow the return "
                    "instructions provided by the recall team."
                ),
            }
            email_action = None
            if customer.email:
                email_action = request_action(
                    self.db,
                    tenant_id=incident.tenant_id,
                    incident_id=incident.id,
                    agent_id="customer-agent",
                    action_type="customer.notify_email",
                    target_type="customer",
                    target_id=customer.id,
                    risk_class="R2",
                    payload=base_payload,
                )
                if email_action.status not in {"APPROVAL_REQUIRED", "BLOCKED"}:
                    execute_action(self.db, email_action)
                    if email_action.status == "SUCCEEDED":
                        verify_action(self.db, email_action)
                actions.append(email_action)

            delivered = bool(
                self.db.scalar(
                    select(Notification.id).where(
                        Notification.tenant_id == incident.tenant_id,
                        Notification.incident_id == incident.id,
                        Notification.customer_id == customer.id,
                        Notification.status == "DELIVERED",
                    )
                )
            )
            if not delivered and customer.phone:
                sms_action = request_action(
                    self.db,
                    tenant_id=incident.tenant_id,
                    incident_id=incident.id,
                    agent_id="customer-agent",
                    action_type="customer.notify_sms",
                    target_type="customer",
                    target_id=customer.id,
                    risk_class="R2",
                    payload=base_payload,
                )
                if sms_action.status not in {"APPROVAL_REQUIRED", "BLOCKED"}:
                    execute_action(self.db, sms_action)
                    if sms_action.status == "SUCCEEDED":
                        verify_action(self.db, sms_action)
                actions.append(sms_action)

            delivered = bool(
                self.db.scalar(
                    select(Notification.id).where(
                        Notification.tenant_id == incident.tenant_id,
                        Notification.incident_id == incident.id,
                        Notification.customer_id == customer.id,
                        Notification.status == "DELIVERED",
                    )
                )
            )
            if delivered:
                existing_return = self.db.scalar(
                    select(ReturnCase).where(
                        ReturnCase.tenant_id == incident.tenant_id,
                        ReturnCase.incident_id == incident.id,
                        ReturnCase.order_id == order.id,
                    )
                )
                if not existing_return:
                    self.db.add(
                        ReturnCase(
                            tenant_id=incident.tenant_id,
                            incident_id=incident.id,
                            customer_id=customer.id,
                            order_id=order.id,
                            status="OPEN",
                        )
                    )

        audit(
            self.db,
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            actor_type="agent",
            actor_id="customer-agent",
            event_type="customer.notifications.processed",
            payload={"actions": len(actions)},
        )
        self.db.commit()
        RecallWorkflow(self.db).refresh_verification_coverage(incident)
        return actions
