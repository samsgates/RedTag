from fastapi import APIRouter

from app.api.routes import agents, approvals, connectors, health, incidents, operations, policies, returns, security

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(agents.router)
api_router.include_router(connectors.router)
api_router.include_router(policies.router)
api_router.include_router(approvals.router)
api_router.include_router(incidents.router)
api_router.include_router(operations.router)
api_router.include_router(returns.router)
api_router.include_router(security.router)
