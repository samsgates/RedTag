from fastapi import APIRouter, Depends

from app.core.security import Principal, get_principal

router = APIRouter(prefix="/agents", tags=["agents"])

AGENTS = [
    {"id": "incident-agent", "name": "Incident Agent", "version": "1.0.0", "model": "gemini-3.5-flash", "capabilities": ["evidence.extract", "incident.classify"], "tools": [], "status": "READY"},
    {"id": "trace-agent", "name": "Trace Agent", "version": "1.0.0", "model": "gemini-3.5-flash", "capabilities": ["supply.trace.plan"], "tools": ["supply.read"], "status": "READY"},
    {"id": "risk-agent", "name": "Risk Agent", "version": "1.0.0", "model": "gemini-3.5-flash", "capabilities": ["recall.simulate"], "tools": ["analytics.read"], "status": "READY"},
    {"id": "containment-agent", "name": "Containment Agent", "version": "1.0.0", "model": "gemini-3.5-flash", "capabilities": ["inventory.quarantine", "shipment.hold"], "tools": ["inventory", "shipment"], "status": "READY"},
    {"id": "customer-agent", "name": "Customer Agent", "version": "1.0.0", "model": "gemini-3.5-flash", "capabilities": ["customer.notify", "delivery.recover"], "tools": ["notification"], "status": "READY"},
    {"id": "logistics-agent", "name": "Logistics Agent", "version": "1.0.0", "model": "gemini-3.5-flash", "capabilities": ["return.coordinate"], "tools": ["returns"], "status": "READY"},
    {"id": "verification-agent", "name": "Verification Agent", "version": "1.0.0", "model": "gemini-3.5-flash", "capabilities": ["action.verify"], "tools": ["connector.readback"], "status": "READY"},
]


@router.get("")
def list_agents(principal: Principal = Depends(get_principal)) -> list[dict]:
    return [{**agent, "tenant_id": principal.tenant_id} for agent in AGENTS]
