# BAND Room Master Orchestration Prompt: Stage 1 (Chunked Orchestration)

## Prompt Overview
This document contains the exact master task prompt to be pasted into the **BAND Desktop** room to initiate autonomous execution of **Stage 1 (Pocketful Track)**. 

In strict adherence to the Dark Factory Hackathon rules, this prompt is the **sole human interaction** with the band. It directs `@polyphony-architect` to coordinate the seat topology using a **sequential chunked orchestration model (B1–B6)** with an interim ledger Q-gate and final certification gate.

---

## Master Task Prompt Text

*(Copy and paste the text block below directly into the BAND Desktop room session)*

```text
@polyphony-architect You are the System Architect and Coordinator for our autonomous software engineering band.

### CHALLENGE & STAGE
- Track: Pocketful (Venmo-style wallet and double-entry ledger)
- Stage: Stage 1 — Core Payments, Settlements, and Idempotent Ledger API
- Target Workspace: ./stage-1/
- Execution Mode: Pure Dark Factory (Zero Human Intervention). Do not request human confirmation, steering, or approvals.

### CORE SEAT MANDATES & FACTORY TOPOLOGY
You must orchestrate the team and enforce strict separation of duties. Under no circumstances should you implement production code directly:
1. @polyphony-architect (You): Ingest specifications, prepare self-contained interface and transaction briefs, ensure @polyphony-developer and @polyphony-qa are present in this room, delegate tasks sequentially, supervise verification loops, verify checkpoint commits in git log, and publish the final stage completion report.
2. @polyphony-developer: Implement the production Go service in ./stage-1/, compile static zero-egress binaries, implement the database transaction logic, build Docker containers, run local tests, and report atomic Git commits for each chunk.
3. @polyphony-qa: Independently inspect committed revisions, verify container startup and execution under `--network none`, run the Stage 1 test harness, execute concurrency burst tests, verify monetary conservation, and report either structured defect rejections or an audit certificate.

### CRITICAL ORCHESTRATION PROTOCOL: SEQUENTIAL CHUNKED BRIEFS
DO NOT post a single monolithic brief for the entire stage. Monolithic turns exceed agent tool-time limits and cause timeouts.
You MUST decompose Stage 1 into the following 6 sequential implementation briefs (B1–B6) and 2 QA validation gates.
Every developer turn MUST finish within ~5 minutes, make an atomic git checkpoint commit, and conclude by tagging @polyphony-architect with "DONE: commit <SHA>" or "PARTIAL: remaining <list>".
You (@polyphony-architect) must run `git log -n 1 --oneline` to verify each commit SHA before dispatching the subsequent brief.

---

### BRIEF SPECIFICATIONS:

#### Brief 1 (B1): Schema DDL, Auth & User Accounts
- Scope:
  - SQLite schema DDL creation in `./stage-1/` using pure-Go `modernc.org/sqlite` (WAL mode, busy_timeout=5000, synchronous=NORMAL, foreign_keys=ON).
  - Tables: system_config, users, sessions, accounts (balance >= 0 check), settlement_operators, transactions, postings, payments, requests, splits, split_shares, settlements, idempotency_keys.
  - Endpoints: GET /health (200), POST /auth/signup (password hashing, unique email/handle), POST /auth/login (session token creation), GET /me (returns authenticated user and balance).
- Developer Action: Implement in ./stage-1/, compile (`go build ./...`), commit as `feat(stage-1): implement schema ddl, auth, and user endpoints`, tag @polyphony-architect with DONE + commit SHA.

#### Brief 2 (B2): Core Payments, Idempotency & Double-Entry Invariants
- Scope:
  - POST /payments endpoint with idempotency key handling (scoped to user, method, path, key).
  - Serialization: Use BEGIN IMMEDIATE or application write mutex.
  - Atomic debit/credit guard: `UPDATE accounts SET balance = balance - :amount WHERE user_id = :id AND balance >= :amount` (return 409 insufficient_funds if zero rows affected).
  - Double-entry postings: Insert balanced postings with sum(amount) == 0.
  - Verbatim payment notes, public and private visibility handling.
- Developer Action: Implement, compile, verify balance invariants, commit as `feat(stage-1): implement core payments, idempotency, and double-entry postings`, tag @polyphony-architect with DONE + commit SHA.

#### INTERIM QUALITY GATE (Q-Gate after B2):
- Scope: @polyphony-architect tags @polyphony-qa to audit the core ledger invariants committed in B1+B2 before advancing to B3.
- QA Action: @polyphony-qa inspects the committed revision, runs unit/concurrency tests on payments, verifies that balances cannot go negative, confirms sum(postings) == 0, and tags @polyphony-architect with "INTERIM AUDIT PASS: ledger invariants verified" (or structured defect rejection).

#### Brief 3 (B3): Peer-to-Peer Requests API
- Scope:
  - Endpoints:
    - POST /requests: create pending payment request for a known handle.
    - POST /requests/{id}/pay: payer fulfills request (idempotent, triggers payment move and updates status to paid).
    - POST /requests/{id}/decline: payer declines pending request.
    - POST /requests/{id}/cancel: requester cancels pending request.
    - GET /requests: list caller's involved requests with status (pending, paid, declined, cancelled) and direction (incoming, outgoing) filters and pagination.
- Developer Action: Implement, compile, test request lifecycles, commit as `feat(stage-1): implement payment requests lifecycle and listing`, tag @polyphony-architect with DONE + commit SHA.

#### Brief 4 (B4): Bill Splits & Batch Operator Settlements
- Scope:
  - POST /splits: divide amount across unique handles (base share + remainder distributed to first handles in input order; create pending requests for non-creator participants).
  - POST /settlements: operator-only batch transfer execution (1..32 transfers, atomic all-or-none net affordability check across all affected wallets, zero 500 errors).
- Developer Action: Implement, compile, verify settlement atomicity, commit as `feat(stage-1): implement splits and batch operator settlements`, tag @polyphony-architect with DONE + commit SHA.

#### Brief 5 (B5): Social Activity Feed & Unicode/Privacy Rules
- Scope:
  - GET /activity: global and social feed displaying public payments or payments where caller is sender/receiver. Never expose requests in feed. Pagination (limit, offset) and reverse chronological ordering.
  - Strict input validation: RFC 3339 timestamps, Unicode notes handling, error envelopes `{"error": {"code": "...", "message": "..."}}`.
- Developer Action: Implement, compile, verify feed privacy filters, commit as `feat(stage-1): implement activity feed and input validation`, tag @polyphony-architect with DONE + commit SHA.

#### Brief 6 (B6): Test Fixtures, State Export/Import & Offline Docker Container
- Scope:
  - POST /_test/reset: resets database to initial fixture and validates non-negative balances.
  - GET /_test/export & POST /_test/import: atomic full-state serialization and restore.
  - Docker packaging: verify static binary build in multi-stage Dockerfile (`CGO_ENABLED=0`), run container under `docker run --network none`, verify offline boot.
- Developer Action: Implement test endpoints, build Docker image `factory-stage1:latest`, test container execution, commit as `feat(stage-1): implement test endpoints and offline docker build`, tag @polyphony-architect and @polyphony-qa with DONE + commit SHA and exact verification instructions.

---

### FINAL QUALITY GATE (Q-Final after B6):
- Scope: Full independent verification by @polyphony-qa.
- QA Action:
  1. Pull final committed revision and build container `docker build -t factory-stage1:latest stage-1/`.
  2. Boot container under `docker run --network none -d -p 8080:8080 factory-stage1:latest`.
  3. Execute automated test suite / harness check (`python -m harness check . --track pocketful`).
  4. Run 10 concurrent payments against a single wallet to verify concurrency serialization (exactly 1 succeeds with 201, 9 fail with 409 insufficient_funds, zero 500 errors).
  5. Check total monetary conservation (sum(balances) == fixture total).
  6. Post raw command outputs and either issue the formal "AUDIT CERTIFICATE: PASS" or defect rejection logs.

### STAGE COMPLETION:
When @polyphony-qa issues the Audit Certificate, @polyphony-architect posts the comprehensive Stage 1 Completion Report to the room, detailing:
- Final commit SHA
- Test suite outcomes and raw pass counts
- Concurrency and conservation verification evidence
- Docker zero-egress compliance confirmation

Begin now, @polyphony-architect, by verifying participant presence and posting Brief 1 (B1) to @polyphony-developer.
```

---

## Key Guardrails & Anti-Pattern Defenses
1. **Chunk Sizing (< 5 min/brief)**: Eliminates the monolithic 900s turn timeout failure mode by constraining each brief to 1-2 modules.
2. **Explicit Mention Handshake**: Guarantees that the architect wakes up after every developer chunk by mandating `@polyphony-architect` in developer completion tags.
3. **Interim Ledger Gate**: Validates core monetary invariants (zero-sum, no overdrafts) early before higher-level features (requests, splits, settlements) are layered on top.
4. **Git Checkpoint Traceability**: Every chunk produces an auditable git commit verified by the architect before subsequent work begins.
