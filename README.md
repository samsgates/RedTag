# RedTag

## Autonomous Product Recall Command Center

**RedTag detects product risk, traces affected inventory and customers, executes policy-authorized containment, recovers from operational failures, and independently verifies every critical action.**

> No action without evidence. No completion without proof.

RedTag is designed for the Google Cloud All Things Agentic Hackathon and for real production-oriented enterprise engineering. It is not a chatbot wrapper. It is an event-driven operational control plane with durable state, bounded agent permissions, typed connectors, action receipts, independent verification, and a Recall Proof Graph.

---

## Why RedTag exists

A defect report is only the beginning of a product recall. Teams still have to answer:

- Which supplier component failed?
- Which supplier lots are affected?
- Which manufacturing batches used the component?
- Which finished products contain those batches?
- Where is inventory currently located?
- Which shipments should be stopped?
- Which customers are exposed?
- Which notifications failed?
- Which products have been recovered?
- Which actions were actually completed?
- Can the organization prove completion to an auditor?

Traditional systems spread this workflow across quality systems, ERP, WMS, CRM, email, logistics platforms, spreadsheets, supplier portals, and human coordination.

RedTag creates one governed agentic workflow around that operational reality.

---

# Core loop

```text
OBSERVE
   |
   v
UNDERSTAND
   |
   v
TRACE
   |
   v
SIMULATE
   |
   v
AUTHORIZE
   |
   v
ACT
   |
   v
RECOVER
   |
   v
VERIFY
   |
   v
PROVE
```

The model is never the system of record. PostgreSQL stores operational truth. Connectors perform mutations. Verification re-reads authoritative state. Every mutation produces an Action Receipt.

---

# Key capabilities

## Multimodal incident intake

Evidence can include images, PDFs, spreadsheets, emails, QA reports, supplier notices, and operator descriptions. Cloud Storage is used for production evidence storage. Local development stores evidence under `.redtag/evidence`.

## Multi-agent reasoning

Google ADK agent definitions are provided for:

- Incident Agent
- Trace Agent
- Risk Agent
- Containment Agent
- Customer Agent architecture
- Logistics Agent architecture
- Compliance Agent architecture
- Security Agent controls
- Verification Agent

The repository includes working ADK definitions for the core reasoning agents and a durable domain workflow that intentionally keeps operational state outside agent memory.

## Deterministic supply tracing

The Trace Agent may decide where to search, but persistent supply-chain edges require provenance. RedTag does not let an LLM invent operational graph truth.

## Recall Director autopilot

After evidence is uploaded, `POST /api/v1/incidents/{id}/autopilot` runs the safe autonomous portion of the recall. In local mode it executes inline. With Pub/Sub enabled it writes a durable command through the transactional outbox, the worker publishes it, and the subscriber resumes the workflow from authoritative incident state.

The Recall Director automatically performs triage, supply tracing, and simulation, then stops at the configured scope-approval gate. After an approver selects a strategy, containment executes and RedTag automatically resumes customer notification and delivery-failure recovery. Physical product returns and final closure remain explicit external or authorized gates.

This design means process restarts and Pub/Sub redelivery do not require the LLM to remember where the recall was. The database state machine and idempotent actions determine the next valid step.

## Counterfactual recall simulation

RedTag compares alternative containment scopes such as:

- one manufacturing batch
- related affected batches
- full product family

Each option includes exposure, estimated coverage, cost estimate, and residual risk.

## Policy-controlled autonomy

Actions are classified R0 through R4. Tenant autonomy level plus deterministic policy decides whether the action is:

- allowed automatically
- approval required
- denied

Bulk customer export and arbitrary shell or SQL capabilities are denied by the built-in policy layer.

## Action Receipt protocol

Every state-changing tool operation records:

- tenant
- incident
- agent
- tool
- action type
- target
- policy decision
- idempotency key
- before-state hash
- after-state hash
- external reference
- execution status
- verification status

## Independent verification

A tool returning success does not make an action verified. The Verification Agent path performs authoritative readback and stores a separate Verification record.

## Recall Proof Graph

The Proof Graph links:

```text
Evidence -> Finding -> Trace -> Decision -> Action -> Receipt -> Verification
```

Every node can reference the underlying operational record.

## Failure-safe asynchronous architecture

The repository includes:

- transactional outbox
- Pub/Sub publisher and durable streaming subscriber
- Recall Director autopilot that advances incidents until the next safety or physical-world gate
- correlation IDs
- idempotency constraints
- durable action history
- explicit state machine
- retry-ready connector boundary

## Prompt-injection controls

External content is always untrusted. The code includes:

- evidence/instruction separation
- local indirect prompt-injection detection
- prohibited capability policy
- typed tool boundaries
- structured model outputs
- PII export denial
- Google Cloud Model Armor text, PDF, DOCX, and XLSX screening with fail-closed mode

---

# Technology stack

## AI and Google Cloud

- Gemini 3.5 Flash
- Google Agent Development Kit 2.5.0
- Google Gen AI SDK 2.13.0
- Vertex AI mode by default for production AI
- Cloud Run for API, web, outbox worker, and migration job
- Cloud SQL for PostgreSQL
- Pub/Sub
- Cloud Storage
- Secret Manager
- Cloud Logging, Monitoring, and Trace integration points
- Terraform Google provider

## Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2
- PostgreSQL 17
- Alembic
- Pydantic 2
- Psycopg 3
- structlog
- OpenTelemetry libraries
- pytest
- Ruff
- mypy

## Frontend

- Next.js 16.2.12
- React 19
- Firebase Authentication SDK 12.16.0
- TypeScript
- Lucide icons
- dependency-light custom design system

---

# Repository layout

```text
redtag/
|
+-- apps/
|   +-- web/                       Next.js command center
|
+-- services/
|   +-- agent_runtime/              deployable Google ADK Agent Runtime app
|   +-- api/
|       +-- app/
|           +-- agents/            ADK, Gemini and AI safety
|           +-- api/routes/        HTTP API
|           +-- connectors/        typed enterprise connectors
|           +-- core/              config, auth, logging
|           +-- db/                SQLAlchemy session and base
|           +-- models/            domain schema
|           +-- schemas/           API and agent contracts
|           +-- services/          workflow, actions, policy, storage
|       +-- alembic/               database migrations
|
+-- packages/contracts/            event schemas
+-- infra/terraform/               Google Cloud infrastructure
+-- demo/                           synthetic scenarios
+-- docs/
|   +-- architecture/              high-level and low-level design
|   +-- adr/                       architecture decisions
|   +-- security/                  threat model
|   +-- runbooks/                  operations
+-- scripts/                        seed and smoke tests
+-- tests/                          unit, integration, E2E, security
+-- .github/workflows/              CI and security scanning
```

---

# High-level design

![RedTag layered high-level design](media_resources/hld_diagram.png)

![RedTag complete architecture diagram](media_resources/architech_diagram.png)

```text
                    +-----------------------------+
                    |       RedTag Next.js        |
                    |       Command Center        |
                    +--------------+--------------+
                                   |
                                   v
                    +-----------------------------+
                    |       FastAPI Control       |
                    | Auth | RBAC | Policy | API  |
                    +----+----------+---------+---+
                         |          |         |
                         v          v         v
                 +----------+  +---------+  +-------------+
                 |PostgreSQL|  | Storage |  | Security    |
                 | truth    |  | evidence|  | controls    |
                 +----+-----+  +---------+  +-------------+
                      |
                Transactional Outbox
                      |
                      v
                 Google Pub/Sub
                      |
                      v
             +---------------------+
             | Google ADK / Gemini |
             |   Agent reasoning   |
             +----------+----------+
                        |
         +--------------+----------------+
         |              |                |
         v              v                v
   Incident/Trace    Risk Agent     Containment Agent
         |              |                |
         +--------------+----------------+
                        |
                        v
                Typed Connector Layer
                        |
              +---------+----------+
              |         |          |
              v         v          v
             ERP       WMS        CRM
                        |
                        v
                  Action Receipt
                        |
                        v
               Verification Readback
                        |
                        v
                  Recall Proof Graph
```

See [`docs/architecture/HIGH_LEVEL_DESIGN.md`](docs/architecture/HIGH_LEVEL_DESIGN.md).

---

# Low-level design

## Domain state

`Incident` is the primary aggregate. Important related records are:

- EvidenceArtifact
- EvidenceClaim
- SupplyNode
- SupplyEdge
- InventoryLot
- RecallStrategy
- Approval
- Action
- ActionReceipt
- Verification
- ProofNode
- ProofEdge
- AuditEvent
- SecurityEvent
- OutboxEvent

See [`services/api/app/models/domain.py`](services/api/app/models/domain.py).

## Incident state machine

```text
NEW
 |
 v
TRIAGING
 |
 v
INVESTIGATING
 |
 v
SCOPE_PROPOSED
 |
 v
AWAITING_APPROVAL
 |
 v
CONTAINING
 |
 v
NOTIFYING
 |
 v
RECOVERING
 |
 v
VERIFYING
 |
 +----> EXCEPTIONS_OPEN
 |
 v
READY_TO_CLOSE
 |
 v
VERIFIED_CLOSED
```

RedTag refuses verified closure unless all critical Action Receipts are independently verified.

## Action execution sequence

```text
Agent requests typed action
        |
        v
Idempotency lookup
        |
        v
Policy evaluation
   |          |
 DENY      APPROVE/ALLOW
   |          |
   v          v
Security    Connector execution
Event          |
               v
          Action Receipt
               |
               v
     Authoritative readback
               |
               v
          Verification
               |
               v
         Proof Graph node
```

See [`docs/architecture/LOW_LEVEL_DESIGN.md`](docs/architecture/LOW_LEVEL_DESIGN.md).

---

# Production principles

## 1. AI proposes. Typed tools execute.

Gemini does not receive arbitrary SQL, shell, or URL execution capability.

## 2. Operational truth is deterministic.

Inventory state, approvals, action status, and verification status live in PostgreSQL and connected systems, not model memory.

## 3. Every mutation is idempotent.

The action idempotency key is derived from tenant, incident, action, target, and action version. PostgreSQL also enforces uniqueness.

## 4. Verification is separate from execution.

The system does not trust an executing agent's natural-language statement that work succeeded.

## 5. Evidence is untrusted.

Uploaded documents can contain malicious text. RedTag treats it as data, not instructions.

## 6. Tenant context comes from identity.

Development mode uses a local principal. Production mode forbids development authentication.

---

# Install and run locally

## Requirements

The recommended local installation uses Docker so PostgreSQL, Python, Node.js, and application dependencies stay isolated. Install:

- Docker 25+
- Docker Compose v2
- Git

For host-based development and production deployment, also install the tools needed for that workflow:

- Python 3.12
- Node.js 22
- Terraform 1.8+
- Google Cloud CLI

## 1. Clone

```bash
git clone https://github.com/YOUR_ORG/redtag.git
cd redtag
```

## 2. Configure

```bash
cp .env.example .env
```

The checked-in defaults use development authentication, local evidence storage, deterministic AI behavior, and simulated notifications. No Google Cloud credentials are required for this mode. Do not reuse these defaults outside local development.

## 3. Start

```bash
make up
```

This builds the images, starts the services in the background, and applies Alembic database migrations before the API accepts traffic:

- PostgreSQL on `localhost:5432`
- FastAPI on `http://localhost:8080`
- Next.js on `http://localhost:3000`
- Outbox worker

Follow startup logs when diagnosing a service that is not ready:

```bash
make logs
```

## 4. Seed the synthetic enterprise

```bash
make seed
```

The dataset creates:

- Northstar Appliances
- Cirrus Components
- X91 Connector
- supplier batch C-771
- manufacturing batches BAT-8831 and BAT-8832
- K100 and K120 product records
- three warehouse inventory lots
- one safety incident
- one intentionally malicious supplier message security event

## 5. Verify the installation

```bash
curl -fsS http://localhost:8080/api/v1/health
curl -fsS http://localhost:8080/api/v1/ready
make smoke
```

The readiness response should report `{"ready":true,"database":"ok"}`, and the smoke test should print the API health response and a nonzero seeded incident count.

## 6. Use RedTag

```text
Web:     http://localhost:3000
API:     http://localhost:8080/api/v1
OpenAPI: http://localhost:8080/docs
```

Open the web application, select the seeded safety incident, inspect its evidence and proposed recall scope, and use Recall Director autopilot to advance the safe workflow. Guarded Autonomy stops before high-impact containment so an approver can review the proposed strategy. The [canonical recall walkthrough](#run-the-canonical-recall) also shows every API operation individually.

## 7. Stop or reset the platform

```bash
# Stop services while preserving the PostgreSQL volume
make down

# Delete local containers and database data for a clean start
docker compose down -v
```

After a reset, run `make up` and `make seed` again.

---

# Run the canonical recall

## Recommended: autonomous workflow

After creating an incident and uploading evidence, let the Recall Director advance all safe phases:

```bash
curl -X POST -H "X-Tenant-ID: tenant_demo" \
  http://localhost:8080/api/v1/incidents/$INCIDENT_ID/autopilot
```

In the default Guarded Autonomy policy, RedTag stops at `AWAITING_APPROVAL`. Approve the recommended strategy or select a strategy ID. After approval, containment executes and the workflow automatically resumes customer notification.

The commands below remain available for operators, debugging, replay, and demonstrations where each phase should be shown separately.

First list the seeded incident:

```bash
curl -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/incidents
```

Save the incident ID as `$INCIDENT_ID`.

## Triage

```bash
curl -X POST -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/incidents/$INCIDENT_ID/triage
```

## Trace supply impact

```bash
curl -X POST -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/incidents/$INCIDENT_ID/trace
```

## Generate counterfactual strategies

```bash
curl -X POST -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/incidents/$INCIDENT_ID/simulate
```

## Execute approved containment

```bash
curl -X POST -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/incidents/$INCIDENT_ID/approve-and-contain
```

Affected inventory lots change from `AVAILABLE` to `QUARANTINED`, and outbound shipments for affected ready-to-ship orders move to `HOLD_RECALL`. Each mutation produces an Action Receipt and is verified through authoritative connector readback.

## Notify affected customers

```bash
curl -X POST -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/incidents/$INCIDENT_ID/notify
```

The synthetic dataset includes successful email delivery, an intentionally failed email that recovers through SMS, and an SMS-only customer. Successful notification creates recovery cases.

## Recover return cases

```bash
curl -H 'X-Tenant-ID: tenant_demo' \
  "http://localhost:8080/api/v1/returns?incident_id=$INCIDENT_ID"

# Repeat for each OPEN return ID
curl -X POST -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/returns/RETURN_ID/recover
```

The incident becomes `READY_TO_CLOSE` only when action verification is complete, every demo recipient has an accepted delivery path, and all required recovery cases are reconciled.

## Inspect proof

```bash
curl -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/incidents/$INCIDENT_ID/proof
```

## Close after operational completion and proof reach 100 percent

```bash
curl -X POST -H 'X-Tenant-ID: tenant_demo' \
  http://localhost:8080/api/v1/incidents/$INCIDENT_ID/close
```

Closure is rejected if critical verification is incomplete.

---

# Using real Gemini

Local deterministic mode intentionally runs without a model so CI, security tests, and the recall workflow remain reproducible.

For real Gemini on Vertex AI:

```dotenv
REAL_AI_ENABLED=true
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=my-project
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-3.5-flash
```

Authenticate locally with Application Default Credentials:

```bash
gcloud auth application-default login
```

The production Gemini adapter is [`services/api/app/agents/gemini.py`](services/api/app/agents/gemini.py).

Important: model output is schema constrained with Pydantic and is not treated as direct operational truth.

---

# Google ADK

Two ADK integration layers are included:

```text
services/api/app/agents/adk_agents.py        scoped application-side agent definitions
services/agent_runtime/app/agent.py          deployable ADK SequentialAgent application
agents-cli-manifest.yaml                     Agent Runtime deployment manifest
```

The deployable reasoning fleet deliberately has no mutation tools. The durable workflow, policy enforcement, idempotency, Action Receipts, and independent verification remain in the RedTag control plane rather than hidden inside prompts.

---

# Authentication

## Development

```dotenv
AUTH_MODE=dev
REDTAG_AUTH_MODE=dev
```

The API uses a synthetic development principal. The local web BFF uses `tenant_demo`, so Docker Compose works without an external identity provider. Development auth is rejected when the API starts with `APP_ENV=production`.

## Production with Google Identity Platform / Firebase Authentication

The web application includes production sign-in for Google and email/password through the Firebase modular web SDK. After sign-in, the browser exchanges the Firebase ID token for a short-lived HTTP-only RedTag web session cookie. Server-rendered pages and browser mutations then pass through the same-origin Next.js BFF, which forwards the bearer token and selected tenant to FastAPI.

FastAPI validates the bearer token using issuer, audience, and JWKS, then verifies that the external identity has an active RedTag `Membership` for the requested tenant. The tenant header alone never grants access.

Example API configuration for Firebase / Google Identity Platform:

```dotenv
APP_ENV=production
AUTH_MODE=oidc
JWT_ISSUER=https://securetoken.google.com/YOUR_FIREBASE_PROJECT_ID
JWT_AUDIENCE=YOUR_FIREBASE_PROJECT_ID
JWKS_URL=https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com
```

Build the production web image with its public Firebase configuration:

```bash
docker build apps/web -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_AUTH_MODE=oidc \
  --build-arg NEXT_PUBLIC_TENANT_ID=your-tenant \
  --build-arg NEXT_PUBLIC_FIREBASE_API_KEY=... \
  --build-arg NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=... \
  --build-arg NEXT_PUBLIC_FIREBASE_PROJECT_ID=... \
  --build-arg NEXT_PUBLIC_FIREBASE_APP_ID=... \
  -t redtag-web:1.0.0
```

Provision the external identity in the RedTag authorization database after creating the user in the identity provider:

```bash
PYTHONPATH=services/api python scripts/provision_user.py \
  --tenant-id acme \
  --tenant-name "Acme Manufacturing" \
  --user-id FIREBASE_UID \
  --email safety@example.com \
  --roles "Owner,Tenant Admin,Quality Manager,Approver"
```

The authorization boundary is implemented in `services/api/app/core/security.py`.

---

# Multi-tenancy

Every business-domain record contains `tenant_id` and every application query includes tenant scope.

PostgreSQL Row-Level Security is included in migration `0002_postgres_tenant_rls.py` for business tables. The authenticated tenant is bound to the SQLAlchemy session, and an `after_begin` hook reapplies the transaction-local `app.tenant_id` setting after every commit. Application query scoping is defense layer one. PostgreSQL RLS is defense layer two. Identity bootstrap tables remain outside RLS so RedTag can validate a user's membership before establishing tenant context.

Never trust a tenant ID supplied only in a request body.

---

# Policy model

The built-in policy engine is intentionally deterministic.

| Risk | Meaning | Default behavior |
|---|---|---|
| R0 | Read only | Allow |
| R1 | Low-risk reversible | Allow at guarded autonomy |
| R2 | Operational mutation | Allow at guarded autonomy within thresholds |
| R3 | High impact | Require approval |
| R4 | Legal or financial sensitivity | Require explicit approval |

The following capabilities are prohibited by default:

- `customer.bulk_export`
- `system.shell`
- `system.sql`

Production tenants can extend the policy layer while retaining the same `PolicyDecision` contract.

---

# Connector framework

A connector implements:

```python
class Connector:
    def health(self) -> dict: ...
    def execute(self, action: str, target_id: str, payload: dict) -> ConnectorResult: ...
    def verify(self, action: str, target_id: str, expected: dict) -> dict: ...
```

The included Inventory, Shipment, and Notification connectors demonstrate mutation, failure handling, and authoritative readback. Notification delivery supports deterministic local simulation plus SMTP/webhook production adapters.

When adding a new enterprise connector, define:

1. supported typed actions
2. risk class for each action
3. input and output schema
4. idempotency behavior
5. retryable and permanent failures
6. rate limit behavior
7. verification method
8. required permissions
9. data classification
10. audit behavior

Do not expose a generic arbitrary URL or command executor directly to the model.

---

# Evidence security

Evidence uploads are content hashed with SHA-256.

Production evidence uses Cloud Storage when `GCS_EVIDENCE_BUCKET` is set.

Text evidence is scanned by RedTag's deterministic indirect prompt-injection detector. When `MODEL_ARMOR_ENABLED=true`, text, PDF, DOCX, and XLSX evidence are also screened through the configured Google Cloud Model Armor template. `MODEL_ARMOR_FAIL_CLOSED=true` records a blocking security event when cloud screening is unavailable.

The included malicious supplier fixture is:

```text
demo/scenarios/malicious_supplier_email.txt
```

It attempts to instruct the system to ignore policy and export the customer database. RedTag records a blocked security event instead of giving the text authority over tools.

---

# Transactional outbox and Pub/Sub

Incident creation writes an OutboxEvent in the same transaction as operational state.

The worker service combines two durable responsibilities:

```text
services/api/app/worker.py                 transactional outbox publisher
services/api/app/services/subscriber.py   Pub/Sub workflow command subscriber
services/api/app/worker_service.py         Cloud Run lifecycle and health service
```

Committed outbox rows are published to Pub/Sub. Autopilot command events are consumed by the subscriber, which binds the event tenant to PostgreSQL RLS and resumes the incident from persisted state. Duplicate delivery remains safe because operational mutations use deterministic idempotency keys.

Configure:

```dotenv
PUBSUB_ENABLED=true
GOOGLE_CLOUD_PROJECT=my-project
PUBSUB_TOPIC=redtag-domain-events
PUBSUB_SUBSCRIPTION=redtag-domain-worker
```

Consumers must be idempotent because Pub/Sub provides at-least-once delivery behavior in common configurations.

---

# Observability

Every HTTP request receives `X-Request-ID`. The backend uses structured JSON logging with structlog.

The architecture carries identifiers for:

- request
- tenant
- incident
- action
- event
- agent
- correlation
- causation

Recommended production dashboards:

- incident time to containment
- verification coverage
- action failures
- duplicate-action prevention
- agent latency
- model schema failures
- Pub/Sub oldest unacked message
- connector error rate
- security policy denials
- prompt-injection blocks

---

# API overview

Core endpoints:

```text
GET    /api/v1/health
GET    /api/v1/ready

POST   /api/v1/incidents
GET    /api/v1/incidents
GET    /api/v1/incidents/{id}
POST   /api/v1/incidents/{id}/evidence
POST   /api/v1/incidents/{id}/autopilot
POST   /api/v1/incidents/{id}/triage
POST   /api/v1/incidents/{id}/trace
POST   /api/v1/incidents/{id}/simulate
POST   /api/v1/incidents/{id}/approve-and-contain?strategy_id=...
POST   /api/v1/incidents/{id}/notify
POST   /api/v1/incidents/{id}/close
GET    /api/v1/incidents/{id}/actions
GET    /api/v1/incidents/{id}/strategies
GET    /api/v1/incidents/{id}/proof
GET    /api/v1/incidents/{id}/timeline

GET    /api/v1/returns
POST   /api/v1/returns/{id}/recover
GET    /api/v1/approvals
POST   /api/v1/approvals/{id}/approve
POST   /api/v1/approvals/{id}/reject

GET    /api/v1/inventory
GET    /api/v1/shipments
GET    /api/v1/customers
GET    /api/v1/notifications
GET    /api/v1/agents
GET    /api/v1/connectors
GET    /api/v1/policies
GET    /api/v1/security/events
```

Interactive OpenAPI is available at `/docs`. Browser-side mutations use the same-origin Next.js `/api/redtag/*` BFF so production identity tokens are not exposed to arbitrary cross-origin JavaScript.

---

# Database migrations

Run:

```bash
alembic -c services/api/alembic.ini upgrade head
```

Create a new migration after model changes:

```bash
alembic -c services/api/alembic.ini revision --autogenerate -m "describe change"
```

Production deployments should never use `create_all()` outside initial/bootstrap migrations.

---

# Testing

Run commands from the repository root unless a step explicitly changes directory.

## Backend setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Start PostgreSQL and configure the host-based test process to use its exposed port:

```bash
docker compose up -d postgres
export DATABASE_URL=postgresql+psycopg://redtag:redtag@localhost:5432/redtag
export AUTH_MODE=dev
export JWT_SECRET=test-only
```

## Reproduce backend CI

```bash
ruff check services tests scripts
mypy services/api/app --ignore-missing-imports
alembic -c services/api/alembic.ini upgrade head
PYTHONPATH=services/api python scripts/seed_demo.py
python -m pytest
```

Run one test module or one test by node ID while iterating:

```bash
python -m pytest tests/unit/test_policy.py
python -m pytest tests/unit/test_policy.py::test_bulk_export_denied
```

Test groups are organized under `tests/unit`, `tests/integration`, `tests/security`, and `tests/e2e`.

## Validate the web application

Frontend commands must run inside `apps/web`; there is no root `package.json`.

```bash
cd apps/web
npm install
npm run typecheck
npm run build
cd ../..
```

## Validate containers and the running stack

```bash
docker compose build
make up
make seed
make smoke
```

The same checks run in GitHub Actions through `.github/workflows/ci.yml`.

## Test command summary

```bash
make test       # Python test suite; host dependencies must be installed
make lint       # Ruff checks
make typecheck  # Backend mypy checks
make build      # Build all Docker Compose images
make smoke      # Exercise a running and seeded API
```

To collect Python coverage:

```bash
python -m pytest --cov=services/api/app --cov-report=term-missing
```

---

# Security testing

Security regression areas:

- tenant boundary violations
- RBAC bypass
- prompt injection
- PII exfiltration
- tool capability escalation
- replay attacks
- duplicate delivery
- SSRF in future generic connectors
- forged webhook signatures
- malicious upload types
- model schema bypass
- secret leakage

See [`docs/security/THREAT_MODEL.md`](docs/security/THREAT_MODEL.md).

---

# Google Cloud deployment

The production baseline deploys RedTag to Google Cloud Run. Cloud SQL stores operational state; Cloud Storage stores evidence; Pub/Sub drives durable workflow commands; Secret Manager holds the database URL; and Artifact Registry stores immutable API and web images.

## Production prerequisites

Before deployment, prepare:

- a Google Cloud project with billing enabled
- permission to manage project APIs, IAM, Cloud Run, Cloud SQL, Storage, Pub/Sub, Secret Manager, and Artifact Registry
- Terraform 1.8+ and the Google Cloud CLI
- a Firebase or Google Identity Platform web application
- an intended production web origin, tenant ID, region, and immutable release tag

Authenticate and select the target project:

```bash
export PROJECT_ID=your-gcp-project
export REGION=us-central1
export ENVIRONMENT=prod
export RELEASE_TAG=1.0.0
export REPOSITORY=redtag-${ENVIRONMENT}-containers

gcloud auth login
gcloud auth application-default login
gcloud config set project "$PROJECT_ID"
gcloud services enable \
  serviceusage.googleapis.com \
  cloudresourcemanager.googleapis.com \
  cloudbuild.googleapis.com
```

Use a dedicated deployment identity in CI instead of a personal account. Production teams should also configure a remote, access-controlled Terraform state backend before applying shared infrastructure.

## 1. Configure Terraform

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and replace every example value. In particular, set:

- `project_id`, `region`, and `environment`
- `api_image` and `web_image` using the release tag that will be built below
- `web_origin` and `default_tenant_id`
- `jwt_issuer`, `jwt_audience`, and `jwks_url` for the production identity provider
- `model_armor_template` if cloud evidence screening is enabled

For Firebase, the issuer is `https://securetoken.google.com/PROJECT_ID`, the audience is the Firebase project ID, and the JWKS URL is already illustrated in `terraform.tfvars.example`.

## 2. Bootstrap Artifact Registry

Terraform manages the container repository, but that repository must exist before Cloud Build can push the first images:

```bash
terraform init
terraform plan -target=google_artifact_registry_repository.redtag
terraform apply -target=google_artifact_registry_repository.redtag
cd ../..
```

The targeted apply also enables the Google APIs on which the repository depends.

## 3. Build and push immutable images

Export the Firebase web application values without committing them to the repository:

```bash
export TENANT_ID=your-tenant
export FIREBASE_API_KEY=your-firebase-api-key
export FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
export FIREBASE_PROJECT_ID="$PROJECT_ID"
export FIREBASE_APP_ID=your-firebase-app-id

gcloud builds submit . \
  --config cloudbuild.yaml \
  --substitutions="_REGION=${REGION},_REPOSITORY=${REPOSITORY},_TAG=${RELEASE_TAG},_AUTH_MODE=oidc,_TENANT_ID=${TENANT_ID},_FIREBASE_API_KEY=${FIREBASE_API_KEY},_FIREBASE_AUTH_DOMAIN=${FIREBASE_AUTH_DOMAIN},_FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID},_FIREBASE_APP_ID=${FIREBASE_APP_ID}"
```

The resulting image values for `terraform.tfvars` are:

```text
api_image = "REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/api:RELEASE_TAG"
web_image = "REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/web:RELEASE_TAG"
```

Do not use `latest` for a production rollout; an immutable tag makes review and rollback deterministic.

## 4. Plan and deploy the platform

```bash
cd infra/terraform
terraform fmt -check
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
```

Terraform provisions:

- required Google APIs
- service identities
- Cloud Run API service
- Cloud Run web service
- Cloud SQL PostgreSQL
- Cloud Storage evidence bucket
- Pub/Sub topic and durable worker subscription
- Artifact Registry Docker repository
- Secret Manager database connection URL
- Cloud Run outbox worker and migration job
- Model Armor API and runtime configuration
- IAM roles required for Cloud SQL, Storage, Pub/Sub, Vertex AI, and Model Armor

## 5. Apply database migrations

```bash
MIGRATION_JOB=$(terraform output -raw migration_job)
gcloud run jobs execute "$MIGRATION_JOB" --region "$REGION" --wait
```

Run migrations before directing users to the new release. Never use SQLAlchemy `create_all()` as a production migration mechanism.

## 6. Provision identity and tenant access

Create the operator in Firebase or Google Identity Platform, then provision that external user ID as a RedTag membership. Run the provisioning command from an approved administrative environment with secure Cloud SQL connectivity:

```bash
cd ../..
PYTHONPATH=services/api python scripts/provision_user.py \
  --tenant-id "$TENANT_ID" \
  --tenant-name "Your Organization" \
  --user-id FIREBASE_UID \
  --email operator@example.com \
  --roles "Owner,Tenant Admin,Quality Manager,Approver"
```

The script uses `DATABASE_URL`; do not expose the Cloud SQL database publicly just to run it. Use the Cloud SQL Auth Proxy, a controlled job, or the organization's existing administrative network path.

## 7. Verify the production release

```bash
API_URL=$(terraform -chdir=infra/terraform output -raw api_url)
WEB_URL=$(terraform -chdir=infra/terraform output -raw web_url)

curl -fsS "${API_URL}/api/v1/health"
curl -fsS "${API_URL}/api/v1/ready"
printf 'RedTag web: %s\n' "$WEB_URL"
```

Sign in through the web URL and confirm the expected tenant, connectors, approvals, and security events are visible. Also inspect Cloud Run logs and verify the worker subscription has no growing unacknowledged-message backlog.

## 8. Release updates and rollback

For each release, build a new immutable tag, update `api_image` and `web_image` in `terraform.tfvars`, run `terraform plan`, apply the plan, execute the migration job, and repeat the health checks. To roll back application code, restore the previous image URIs and apply Terraform again. Database rollback requires a migration-specific recovery plan and should not be assumed safe.

## Production wiring notes

Terraform mounts Cloud SQL through the Cloud Run Cloud SQL integration, stores the SQLAlchemy connection URL in Secret Manager, deploys the API, web service, and outbox worker, and creates a migration job. OIDC issuer/audience/JWKS values are required Terraform inputs.

A production rollout should additionally include:

- organization-approved private networking where required by policy
- Secret Manager rotation procedures
- managed TLS
- organization domain and DNS
- WAF/rate limits if externally exposed
- database RLS
- environment-specific IAM
- alerting
- backup restore test
- SLO dashboards

---

# Environment variables

| Variable | Purpose | Local default |
|---|---|---|
| `APP_ENV` | environment safety mode | development |
| `DATABASE_URL` | SQLAlchemy PostgreSQL URL | Docker Postgres |
| `AUTH_MODE` | `dev` or `oidc` | dev |
| `JWT_ISSUER` | token issuer | redtag-local |
| `JWT_AUDIENCE` | API audience | redtag-api |
| `JWT_SECRET` | local HS256 secret only | unsafe local value |
| `JWKS_URL` | production OIDC signing-key endpoint | empty |
| `OIDC_EMAIL_CLAIM` | email claim name | email |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project | empty |
| `GOOGLE_CLOUD_LOCATION` | Vertex location | global |
| `GEMINI_MODEL` | reasoning model | gemini-3.5-flash |
| `REAL_AI_ENABLED` | real Gemini switch | false |
| `GCS_EVIDENCE_BUCKET` | evidence bucket | empty/local filesystem |
| `PUBSUB_ENABLED` | publish outbox events | false |
| `PUBSUB_TOPIC` | domain event topic | redtag-domain-events |
| `PUBSUB_SUBSCRIPTION` | durable workflow subscriber | redtag-domain-worker |
| `MODEL_ARMOR_ENABLED` | enable Google Cloud Model Armor screening | false |
| `MODEL_ARMOR_LOCATION` | Model Armor template region | us-central1 |
| `MODEL_ARMOR_TEMPLATE` | existing Model Armor template ID | empty |
| `MODEL_ARMOR_FAIL_CLOSED` | record a blocking security event when Model Armor is unavailable | true |
| `REAL_NOTIFICATIONS_ENABLED` | enable SMTP/webhook delivery adapters | false |
| `SMTP_HOST` / `SMTP_*` | production email provider connection | empty |
| `NOTIFICATION_WEBHOOK_URL` | non-email delivery adapter webhook | empty |
| `REDTAG_API_URL` | server-side web BFF upstream API | localhost API |
| `REDTAG_AUTH_MODE` | web auth gate, `dev` or `oidc` | dev |

Never use the local defaults in production.

---

# Operational runbooks

See [`docs/runbooks/OPERATIONS.md`](docs/runbooks/OPERATIONS.md) for:

- database outage
- Pub/Sub backlog
- Gemini outage
- connector outage
- verification mismatch
- agent loop
- secret rotation

---

# Architecture decisions

The repository documents important decisions under `docs/adr`:

- PostgreSQL operational source of truth
- Action Receipt protocol
- independent verification
- transactional outbox
- memory separation
- policy-based autonomy

These are invariants. A future implementation should not move operational truth into prompt context or agent memory.

---

# Production hardening checklist

Before accepting real customer data:

- [ ] Configure Google Identity Platform/Firebase Authentication or another verified OIDC/JWKS provider and provision tenant memberships.
- [x] Apply PostgreSQL tenant RLS migration and validate production application role ownership/permissions.
- [ ] Review whether organization policy requires private-IP Cloud SQL networking beyond the Cloud Run Cloud SQL connector.
- [ ] Inject all secrets from Secret Manager.
- [ ] Configure region/data-residency policy.
- [ ] Configure malware scanning for file uploads.
- [ ] Add organization-specific Model Armor policy.
- [ ] Configure Cloud Armor/API protection if public.
- [ ] Enable alerting for failed actions and verification mismatches.
- [ ] Configure Pub/Sub dead-letter topic and replay procedures.
- [ ] Run backup restoration test.
- [ ] Add real ERP/WMS/CRM connector contract tests.
- [ ] Add legal/compliance approval policies for target jurisdictions.
- [ ] Validate outbound notification consent and template policy.
- [ ] Complete penetration testing.
- [ ] Review dependency and container scan results.
- [ ] Establish incident response and vulnerability disclosure ownership.

This checklist is intentionally explicit. Production-ready software still requires production environment configuration and organization-specific controls.

---

# Hackathon demo scenario

The repository's synthetic scenario is designed to show the complete agentic loop:

1. A quality incident reports an overheated X91 connector.
2. Gemini or deterministic test mode identifies supplier batch C-771.
3. Trace resolves BAT-8831 and BAT-8832.
4. Risk Agent presents three recall strategies.
5. The affected-batch strategy is recommended.
6. Containment quarantines inventory and holds affected outbound shipments.
7. Each mutation generates an Action Receipt and independent readback verification.
8. Customer Agent sends recall notifications and recovers an intentionally failed email through SMS.
9. Successful notifications create return cases that are reconciled through product recovery.
10. A malicious supplier instruction attempts PII export.
11. Security policy blocks it before tool execution.
12. Recall Proof Graph shows the verified operational chain.
13. Incident can close only when critical actions are verified, demo recipients are reached, and required return cases are recovered.

This demonstrates a system that performs work rather than merely describing work.

---

# What is implemented versus extension points

## Implemented in this repository

- production-oriented FastAPI control plane
- tenant-scoped domain model
- incident lifecycle
- evidence storage abstraction
- baseline prompt-injection detection
- supply graph model
- provenance-backed deterministic supply tracing for arbitrary tenant genealogy data
- data-backed counterfactual strategy model with explicit cost assumptions
- policy engine
- inventory, shipment, and notification connectors
- customer notification retry/fallback workflow
- product return/recovery cases
- approval center and approval APIs
- generic OIDC/JWKS authorization with membership checks
- Firebase / Google Identity Platform web sign-in and same-origin BFF
- idempotent action request
- Action Receipts
- independent verification readback
- Proof Graph
- audit timeline
- security events
- transactional outbox
- Pub/Sub publisher and durable autopilot subscriber
- Recall Director autonomous state resumption
- Google Gen AI structured-output adapter
- Google ADK agent definitions
- Next.js command center with incident, agent, approval, operations, proof, security, and governance views
- deployable ADK Agent Runtime application
- Docker Compose
- Terraform production baseline with Cloud Run, Cloud SQL, Artifact Registry, Pub/Sub, Storage, Secret Manager, RLS migration, and Model Armor wiring
- CI and security workflows
- tests and synthetic fixtures
- architecture, threat-model, ADR, and runbook documentation

## Production integration points requiring organization configuration

- real ERP/WMS/CRM connectors
- organization-specific regulatory policies
- SMTP/webhook credentials and approved production notification templates
- organization-specific Model Armor template policy and tuning
- Agent Platform identity/gateway/registry deployment
- private networking topology
- production DNS and TLS ownership

These cannot be safely hard-coded because they depend on the organization, region, identity provider, and enterprise systems.

---

# Local security note

`AUTH_MODE=dev` exists only for reproducible local development. The application refuses to start in production when development auth is selected.

Never expose a development-mode RedTag API to the public internet.

---

# Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

Mutation tools must include:

- a defined capability name
- typed input
- risk class
- policy behavior
- idempotency strategy
- verification implementation
- tests

---

# Security reporting

See [`SECURITY.md`](SECURITY.md). Do not publish vulnerabilities in a public issue before coordinated disclosure.

---

# License

Apache License 2.0. See [`LICENSE`](LICENSE).

---

# Product philosophy

RedTag should never become "ChatGPT for product recalls."

Its purpose is to demonstrate trustworthy operational autonomy:

> An AI-generated statement is not proof. An attempted action is not completion. An autonomous enterprise agent becomes useful when it can act within policy, recover when systems disagree with its plan, and independently prove what actually happened.

---

# Artifact verification and dependency inventory

The generated repository includes two release-support documents:

- [`BUILD_REPORT.md`](BUILD_REPORT.md). Exact checks executed in the generation environment, plus explicit checks that require a connected CI/Google Cloud environment.
- [`docs/DEPENDENCIES.md`](docs/DEPENDENCIES.md). Direct dependency versions, purposes, and the production supply-chain locking policy.

For long-running production workers, RedTag serializes execution per tenant/incident with a PostgreSQL session advisory lock. This prevents concurrent HTTP/Pub/Sub deliveries from independently advancing the same recall while still allowing separate incidents to execute in parallel. The database state machine and idempotency keys remain the recovery source of truth.
