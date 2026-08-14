# Dependency Inventory

RedTag pins every direct runtime and development dependency in the repository manifests. Transitive dependency locks should be generated in the connected build environment before a production release because this build sandbox cannot reach public package registries.

## Backend runtime

| Package | Version | Purpose |
|---|---:|---|
| fastapi | 0.133.0 | HTTP control plane |
| uvicorn[standard] | 0.35.0 | ASGI server |
| pydantic | 2.12.5 | API and agent contracts |
| pydantic-settings | 2.10.1 | environment configuration |
| sqlalchemy | 2.0.43 | persistence and transaction layer |
| psycopg[binary,pool] | 3.2.9 | PostgreSQL driver |
| alembic | 1.16.4 | database migrations |
| python-multipart | 0.0.20 | evidence uploads |
| httpx | 0.28.1 | outbound HTTP adapters |
| tenacity | 9.1.2 | bounded retry primitives |
| structlog | 25.4.0 | structured logs |
| orjson | 3.11.2 | JSON responses |
| PyJWT[crypto] | 2.10.1 | OIDC/JWT verification |
| google-auth | 2.56.0 | Google credentials |
| google-cloud-storage | 3.3.0 | evidence storage |
| google-cloud-pubsub | 2.31.1 | durable workflow events |
| google-cloud-secret-manager | 2.24.0 | secret integration support |
| google-cloud-tasks | 2.19.3 | delayed/rate-controlled task integration support |
| google-cloud-modelarmor | 0.7.0 | untrusted evidence screening |
| google-genai | 2.13.0 | Gemini structured multimodal calls |
| google-adk[gcp] | 2.5.0 | agent fleet and Agent Runtime app |
| prometheus-client | 0.22.1 | metrics integration |
| email-validator | 2.2.0 | validated email fields |

## Backend development

| Package | Version | Purpose |
|---|---:|---|
| pytest | 8.4.1 | automated tests |
| pytest-cov | 6.2.1 | coverage |
| ruff | 0.12.8 | lint/import/style checks |
| mypy | 1.17.1 | static type checking |
| types-PyJWT | 1.7.1 | JWT typing |

## Web application

| Package | Version | Purpose |
|---|---:|---|
| next | 16.2.12 | application framework and BFF |
| react | 19.2.0 | UI runtime |
| react-dom | 19.2.0 | React DOM runtime |
| lucide-react | 0.468.0 | icons |
| firebase | 12.16.0 | browser authentication |
| typescript | 5.9.2 | type system/compiler |
| @types/node | 24.2.1 | Node typings |
| @types/react | 19.0.14 | React typings |
| @types/react-dom | 19.0.6 | React DOM typings |

## Infrastructure dependencies

RedTag additionally requires Docker/OCI, Terraform, Google Cloud CLI, Google Agents CLI, PostgreSQL 17, and a Google Cloud project for the production deployment path. See `README.md` and `docs/architecture/AGENT_RUNTIME.md`.

## Supply-chain policy

Before a tagged production release:

1. Generate and commit a Python transitive lock using the organization's approved resolver.
2. Generate and commit `apps/web/package-lock.json` from a connected environment.
3. Run dependency vulnerability and license scans.
4. Generate an SBOM for both runtime images.
5. Pin production container images by digest after CI promotion.

The repository does not fabricate lockfile integrity hashes when registry metadata is unavailable.
