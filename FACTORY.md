# FACTORY.md — Autonomous Software Dark Factory Engineering Report

## Executive Summary
This document provides the master technical specification and operational rationale for our autonomous Software Dark Factory engineered for the **WeAreDevelopers x BAND Dark Factory AI Hackathon** (Pocketful Track). The factory operates completely unassisted inside **BAND Desktop**, orchestrating a three-seat autonomous agent band that converts stage specifications into mathematically verifiable, zero-egress containerized services.

---

## 1. Factory Architecture & Seat Topology

The factory enforces a strict separation of concerns across three distinct seats. In adherence to clean-room dark-factory rules, human involvement is limited strictly to dispatching the initial stage task. No intermediate human steering or code editing is permitted.

```
                      +-----------------------------+
                      |   Stage Task Specification  |
                      |   (Dispatched by Human)     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |      @architect Seat        |
                      | (System Architect & Coord)  |
                      +--------------+--------------+
                                     |
                         Interface & Invariant Brief
                                     |
                                     v
                      +-----------------------------+
                      |      @developer Seat        |
                      | (Software Engineer & Impl)  |
                      +--------------+--------------+
                                     |
                        Committed Revision & Checks
                                     |
                                     v
                      +-----------------------------+
                      |      @qa-auditor Seat       |
                      | (QA Auditor & Sentinel)     |
                      +--------------+--------------+
                                     |
                 +-------------------+-------------------+
                 |                                       |
          Defect Rejection                        Audit Certificate
                 |                                       |
                 v                                       v
         [Back to @developer]                   [Stage Completed]
```

### Seat Specifications

| Seat Identity | Primary Role | Harness | Model | Authority & Responsibilities |
|---|---|---|---|---|
| **@architect** | System Architect & Coordinator | Claude Code | claude-sonnet-5 | Decomposes raw feature specs into formal API schemas, state invariants, and execution sequences; assigns self-contained tasks; rejects plans violating zero-egress isolation; reports final stage completion. |
| **@developer** | Senior Software Engineer & Implementer | Claude Code | claude-sonnet-5 | Implements pure Go source code, writes atomic database transactions, ensures deterministic idempotency, provides UI `data-testid` attributes, writes local unit tests, and commits atomically. |
| **@qa-auditor** | QA Auditor & Verification Sentinel | Claude Code | claude-sonnet-5 | Adversarial verification sentinel; runs automated test suites, concurrency stress checks, and fuzzing; tests containers with `--network none`; rejects regressions with reproduction traces. |

### Inter-Agent Communication Protocol
1. **Self-Contained Handoffs**: Seats communicate strictly using literal `@handles`. Every handoff message contains the full task, specification requirements, constraints, and target paths. Pointers to earlier room messages or instructions to "read the room" are prohibited.
2. **Defect Rejection Loop**: If any automated check or invariant test fails, `@qa-auditor` posts a structured rejection tagging `@developer` with exact failure traces and reproduction commands. `@developer` diagnoses and commits a surgical fix without human intervention.
3. **Audit Certification**: A stage is certified only when 100% of internal and official harness checks pass under isolated network conditions.

---

## 2. Design Rationale & Architectural Decisions

### 2.1 Pure-Go SQLite Driver (`modernc.org/sqlite`)
* **Decision**: Implement all database persistence in Go utilizing `modernc.org/sqlite` instead of `github.com/mattn/go-sqlite3`.
* **Rationale**: Standard SQLite drivers require CGO, binding the build process to external C compilers (gcc/musl) and platform-specific dynamic linking. By using `modernc.org/sqlite` (a pure-Go transpilation of SQLite C source code), the entire application builds with `CGO_ENABLED=0`, producing an immutable, statically linked Linux ELF binary.
* **Trade-off**: Pure-Go SQLite incurs a modest compilation time increase during initial module download, which is mitigated via Docker build layer caching and `-p 1` memory capping.

### 2.2 Mathematically Verifiable Zero-Egress Containerization
* **Decision**: All stage services are packaged as multi-stage Docker builds and must start cleanly with `docker run --network none`.
* **Rationale**: Real-world mission-critical software must operate reliably in isolated clean-room environments without runtime network calls.
* **Implementation Details**:
  - **Stage 1 (Builder)**: Uses `golang:alpine` to fetch dependencies at build time, compile static binaries with `-ldflags="-s -w -extldflags '-static'"`, and embed timezone data (`-tags timetzdata`).
  - **Stage 2 (Runtime)**: Minimal `alpine:3.20` image with an unprivileged runtime user (`appuser:1000`) and a dedicated writable storage volume (`/data/app.db`).
  - **Zero Outbound Access**: Fully boots and functions without external network connectivity.

### 2.3 Double-Entry Ledger & High-Concurrency Architecture (Phase 0.5 Recon)
* **Mathematical Conservation**:
  $$\sum \Delta_{\text{debit}} = \sum \Delta_{\text{credit}} \implies \sum_{p \in T.\text{postings}} p.\text{amount} = 0$$
  Every mutating monetary transfer is modeled as an atomic transaction that produces balanced debit and credit entries.
* **Global Conservation Invariant**:
  $$\sum_{u \in \text{Users}} \text{balance}_u = \text{Seeded Total}$$
  Deposits and withdrawals are out of scope. Money is strictly transferred between valid wallets.
* **Zero Negative Balances Guaranteed**:
  - **SQLite Constraint**: `accounts` table enforces `balance INTEGER NOT NULL CHECK (balance >= 0)`.
  - **Conditional Mutation**: Debits execute via conditional SQL:
    ```sql
    UPDATE accounts 
    SET balance = balance - :amount, updated_at = :now 
    WHERE user_id = :from_id AND balance >= :amount;
    ```
    If `RowsAffected() == 0`, the transaction aborts with `409 insufficient_funds`. Under a burst of 10 simultaneous requests attempting to spend 1,000 from a 1,000 wallet, exactly 1 succeeds and 9 fail with 409 without database deadlocks.

### 2.4 SQLite PRAGMA Configuration for Concurrency
To ensure zero `SQLITE_BUSY` errors during concurrent bursts (50 in-flight requests):
```go
dsn := "file:/data/pocketful.db?" +
    "_pragma=journal_mode(WAL)&" +
    "_pragma=busy_timeout(5000)&" +
    "_pragma=synchronous(NORMAL)&" +
    "_pragma=foreign_keys(ON)&" +
    "_pragma=cache_size(-64000)&" +
    "_pragma=temp_store(MEMORY)"
```
- `journal_mode=WAL`: Write-Ahead Logging decouples readers and writers.
- `busy_timeout=5000`: Waits up to 5,000 ms for write locks to clear instead of failing immediately.
- `synchronous=NORMAL`: Reduces fsync overhead while maintaining full crash safety in WAL mode.
- **Write Serialization**: Go application utilizes `BEGIN IMMEDIATE` or an internal write mutex (`sync.Mutex`) to serialize write transactions, eliminating upgrade lock contention.

### 2.5 API Contract & Idempotency Specification
* **Error Envelope**: Every `4xx` and `5xx` response returns `{"error": {"code": "<code_string>", "message": "<human_text>"}}`.
* **5 Idempotent Write Paths**:
  1. `POST /payments`
  2. `POST /requests`
  3. `POST /requests/{id}/pay`
  4. `POST /splits`
  5. `POST /settlements`
* **Idempotency Semantics**:
  - Scoped to `(user_id, method, path, idempotency_key)`.
  - First execution returns `201 Created`.
  - Exact replay (identical body) returns `200 OK` with the original response body.
  - Replay with altered body returns `409 idempotency_key_reuse`.
  - Failed operations (`4xx`) do not claim keys and permit immediate retry.

### 2.6 Chunked Orchestration Architecture & Timeout Insurance
* **Problem**: Monolithic implementation briefs (e.g., instructing the implementer to synthesize 16 REST endpoints, database schemas, and transactions in a single turn) exhaust agent tool turn timeouts (180s–900s), leaving broken uncompiled code in the working tree. Furthermore, forensic recon of BAND SDK v3.2.0 revealed that platform message delivery (`/next`) strictly filters on explicit `@mentions`; unaddressed platform timeout notices never wake peer agents, leading to permanent room deadlock.
* **Architectural Solution**: Decompose the stage into 6 discrete, timeout-proof implementation briefs (B1–B6) executed sequentially with atomic git checkpoint commits, paired with an interim Q-gate and a final QA certification gate.
* **Autonomous In-Prompt Chunking Protocol**: The entire sequencing protocol is embedded directly within the initial human task prompt, ensuring 100% autonomous dark factory operation without human steering.

```
+---------------------------------------------------------------------------------------------------+
|                                 Sequential Chunked Pipeline                                      |
+---------------------------------------------------------------------------------------------------+
|  [B1] Auth & Identity     --> Checkpoint Commit 1                                                 |
|  [B2] Ledger & Payments   --> Checkpoint Commit 2                                                 |
|       |                                                                                           |
|       v                                                                                           |
|  [Interim Q-Gate]         --> QA validates double-entry conservation & balance invariant early    |
|       |                                                                                           |
|       v                                                                                           |
|  [B3] P2P Requests        --> Checkpoint Commit 3                                                 |
|  [B4] Splits & Settlement --> Checkpoint Commit 4                                                 |
|  [B5] Activity Feed       --> Checkpoint Commit 5                                                 |
|  [B6] Fixtures & Docker   --> Checkpoint Commit 6                                                 |
|       |                                                                                           |
|       v                                                                                           |
|  [Final QA Gate]          --> Concurrency burst, zero-egress container audit, Official Certificate|
+---------------------------------------------------------------------------------------------------+
```

* **Chunk Specification Breakdown**:
  1. **Brief 1 (B1) — Schema DDL & Identity**: Users table, password hashing (bcrypt), session tokens, `POST /signup`, `POST /login`, `GET /me`. Local verification: `go test -run TestAuth`.
  2. **Brief 2 (B2) — Core Double-Entry Payments**: Accounts, transfers, balanced postings ($\sum \text{amount} = 0$), idempotency keys, `POST /payments`, conditional debit check (`balance >= amount`). Local verification: `go test -run TestPayments`.
  3. **Interim Q-Gate**: `@polyphony-qa` activates between B2 and B3 to run adversarial ledger invariant tests. Ensures core accounting is mathematically sound before higher-level features are built atop it.
  4. **Brief 3 (B3) — Peer-to-Peer Requests**: Requests table, `POST /requests`, `POST /requests/{id}/pay` (atomic transfer execution), `POST /requests/{id}/decline`, `POST /requests/{id}/cancel`, `GET /requests`. Local verification: `go test -run TestRequests`.
  5. **Brief 4 (B4) — Bill Splits & Batch Settlements**: Splits and participants tables, `POST /splits`, `GET /splits/{id}`, `POST /settlements` (idempotent batch resolution). Local verification: `go test -run TestSplits`.
  6. **Brief 5 (B5) — Social Activity Feed & Privacy**: Feed generation with visibility filtering (`public` visible to all, `private` isolated to counterparties). Local verification: `go test -run TestFeed`.
  7. **Brief 6 (B6) — Test Fixtures, Harness Endpoints & Docker**: `POST /reset`, `GET /export`, `POST /import`, multi-stage Docker build, zero-egress verification (`docker run --network none`).
* **Handoff & Checkpoint Protocol**:
  - The developer finishes each brief within 3–5 minutes of tool time, commits atomically (`git commit -m "feat(stage-1): ..."`), and posts `@polyphony-architect DONE: commit <SHA>`.
  - The architect verifies the commit (`git log -n 1 --oneline`) before issuing the next brief, ensuring bounded turn duration and zero timeout exposure.

---

## 3. QA Auditor Verification Suite & Inspection Commands

The `@qa-auditor` seat executes independent, adversarial verification using the following exact commands:

### 3.1 Mandate & Repository Offline Conformance Gate
```sh
# Verify generic mandates, absence of forbidden vocabulary, and valid structure
python -m harness check . --track pocketful
```

### 3.2 Clean Container Build & Zero-Egress Execution
```sh
# Build static container image
docker build -t pocketful:stage-1 stage-1/

# Run container with zero network access on port 8080
docker run --rm -d --name pocketful-s1 -p 8080:8080 --network none -e PORT=8080 pocketful:stage-1

# Verify health endpoint returns 200 {"status": "ok"} within 60s
curl -i http://localhost:8080/health
```

### 3.3 Stage 1 Harness Verification Run
```sh
# Execute official test harness against the running or containerized service
python -m harness run --track pocketful --repo . --stage 1 --mode isolated --out checks/s1-audit
```

### 3.4 Concurrency Burst & Balance Conservation Audit
To verify mutual exclusion and mathematical conservation:
1. Seed fixture with Ada (1000 minor units) and Bob (0 minor units).
2. Fire 10 simultaneous asynchronous requests: `POST /payments` (`to_handle: "bob", amount: 1000`).
3. Assert exact outcomes:
   - Exactly one `201 Created`.
   - Exactly nine `409 Conflict` (`error.code: "insufficient_funds"`).
   - Zero `5xx` internal server errors.
   - Ada balance equals 0; Bob balance equals 1000.
   - Global conservation: $\sum \text{balances} == 1000$.

---

## 4. Self-Healing & Failure-Recovery Protocol

The factory operates an automated self-healing feedback loop:
1. **Detection**: `@qa-auditor` executes the verification harness against the newly committed revision inside `--network none`.
2. **Diagnosis**: When a test fails (e.g. permission errors on database creation or schema mismatch), the auditor captures the raw container stderr and exit code.
3. **Autonomous Remediate**: The developer receives the defect trace, identifies the root cause (e.g. non-root file ownership or missing foreign key index), applies the fix, and commits a new revision.
4. **Re-verification**: The cycle repeats until the audit suite produces a clean green run.

---

## 5. Execution Metrics & Economics Tracking

The Dark Factory tracks engineering metrics across each stage:

| Stage | Target Surface | Language / Runtime | Offline Compliance | Status |
|---|---|---|---|---|
| **Stage 0** | Repository Skeleton & Zero-Egress Base | Go 1.24+ / Alpine Static | 100% (`--network none` verified) | **Complete** |
| **Phase 0.5** | Deep Recon, API Contract, SQLite Schema, & Prompt | Go DDL / REST Contract | Verified via Harness & Docs | **Complete** |
| **Stage 1** | Core API & SQLite Ledger Persistence | Go / Pure-Go SQLite | Required (`--network none`) | Planned |
| **Stage 2** | Responsive Web UI + Conformance Test IDs | Go + SSR/Static Assets | Required (`--network none`) | Planned |
| **Stage 3** | Concurrency Hardening & Idempotency Replay | Go Transaction Engine | Required (`--network none`) | Planned |
| **Stage 4** | Advanced Extensions & Full Regression Suite | Go Full Stack | Required (`--network none`) | Planned |

---

## 6. Verification & Compliance Standards

Every stage submission must satisfy:
1. **Gate 1**: Three generic agent mandates in `mandates/` with harness and model identifiers.
2. **Gate 2**: Zero track-specific vocabulary hardcoded in mandate files.
3. **Gate 3**: Stage builds from source inside container without network access.
4. **Gate 4**: Verified room collaboration export recorded in `room.json`.
