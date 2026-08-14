# RedTag High-Level Design

## System objective

RedTag coordinates long-running product recall operations with bounded autonomy. Gemini and Google ADK perform evidence reasoning and task decomposition. Typed connectors execute operational changes. PostgreSQL records authoritative truth. Verification re-reads that truth before an action becomes proof.

## Major components

1. **Next.js Command Center**. Incident, strategy, action, return, proof, security, approval, and operations views.
2. **FastAPI Control Plane**. OIDC authentication, tenant context, RBAC, API contracts, policies, and command handling.
3. **Recall Director Autopilot**. Deterministic state-machine runner that advances safe phases and stops at policy, human, or physical-world gates.
4. **Google ADK Agent Fleet**. Deployable Incident, Trace, and Risk reasoning sequence plus capability-scoped application agents.
5. **Gemini 3.5 Flash**. Multimodal incident extraction and schema-constrained reasoning.
6. **PostgreSQL / Cloud SQL**. Authoritative incident state, genealogy, actions, receipts, approvals, audit, proof graph, and outbox.
7. **PostgreSQL RLS**. Second tenant-isolation layer using a transaction-local tenant context reapplied after every transaction begins.
8. **Transactional Outbox + Pub/Sub**. Durable event publication and workflow-command delivery.
9. **Workflow Worker**. Publishes outbox rows and consumes autopilot commands. Duplicate delivery is safe through idempotent domain operations.
10. **Cloud Storage**. Immutable evidence objects.
11. **Model Armor**. Optional production screening of untrusted text, PDF, DOCX, and XLSX evidence, with configurable fail-closed behavior.
12. **Connector layer**. Bounded inventory, shipment, notification, and future enterprise adapter contracts.
13. **Policy engine**. Deterministic authorization by risk class and autonomy level.
14. **Verification path**. Independent readback after every state-changing connector operation.

## Main operational path

```text
Browser / Operator
       |
       v
Next.js BFF + Firebase/Identity Platform
       |
       v
FastAPI Control Plane
       |
       +---- Evidence ----> Cloud Storage ----> Model Armor
       |
       +---- Domain state --------------------> Cloud SQL/PostgreSQL
       |                                           |
       |                                    Transactional Outbox
       |                                           |
       |                                           v
       |                                        Pub/Sub
       |                                           |
       |                                           v
       |                                    Workflow Worker
       |                                           |
       |                                           v
       +<---------------------------------- Recall Director
                                                   |
                              +--------------------+-------------------+
                              |                    |                   |
                              v                    v                   v
                         Incident Agent        Trace Agent          Risk Agent
                              |                    |                   |
                              +--------------------+-------------------+
                                                   |
                                                   v
                                        Policy + Typed Connectors
                                                   |
                                      +------------+------------+
                                      |            |            |
                                      v            v            v
                                  Inventory     Shipment    Notification
                                      |            |            |
                                      +------------+------------+
                                                   |
                                                   v
                                             Action Receipt
                                                   |
                                                   v
                                      Independent Verification
                                                   |
                                                   v
                                           Recall Proof Graph
```

## Safety gates

RedTag advances automatically only while the current state allows it. In Guarded Autonomy the normal flow stops at recall-scope approval, physical product recovery, unresolved customer-contact exceptions, security holds, and authorized final closure. These are explicit product controls rather than prompt conventions.

## Critical invariant

A successful tool call is not equivalent to a verified fact. A critical operation is complete only when an independent Verification record confirms the expected authoritative state.

## Trust boundaries

External documents, supplier messages, connector data, and model output are untrusted. Model Armor, typed schemas, policy decisions, database constraints, OIDC membership, PostgreSQL RLS, tenant-scoped queries, idempotency, and independent verification form the trusted control path.
