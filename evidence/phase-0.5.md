# Phase 0.5 Evidence Pack — Deep Recon & Open Source Research

## Execution Overview
- **Project**: WeAreDevelopers x BAND Dark Factory Hackathon
- **Track**: Pocketful
- **Phase**: Phase 0.5 — Deep Recon & Open Source Research
- **Timestamp**: 2026-09-27
- **Git HEAD**: `f3d69b1`

---

## 1. Acceptance Verification Matrix

| Task ID | Description | Artifact | Status | Commit Hash |
|---|---|---|---|---|
| **T1** | Harness API Reverse-Engineering | `docs/recon/api-contract.md` | **PASSED** | `6ab5a40` |
| **T2** | Open Source Ledger Pattern Research | `docs/recon/ledger-schema.md` | **PASSED** | `49195ad` |
| **T3** | BAND Room Orchestration Prompt Design | `docs/recon/stage-1-room-prompt.md` | **PASSED** | `87e8fb1` |
| **T4** | Update FACTORY.md with Research Findings | `FACTORY.md` | **PASSED** | `f58014e` |

---

## 2. Git Commit Log (`git log -n 5 --oneline`)

```text
f3d69b1 docs: update STATE.md for phase 0.5 completion
f58014e docs: update FACTORY.md with phase 0.5 research findings
87e8fb1 docs(recon): draft stage-1 band room orchestration prompt
49195ad docs(recon): define optimal sqlite double-entry schema
6ab5a40 docs(recon): map pocketful harness API contract
```

---

## 3. Discovered API Contract (`docs/recon/api-contract.md`)
- Total Endpoints: 16
- Five Idempotent Write Paths:
  1. `POST /payments`
  2. `POST /requests`
  3. `POST /requests/{id}/pay`
  4. `POST /splits`
  5. `POST /settlements`
- Error Envelope: `{"error": {"code": "<error_code>", "message": "<human_text>"}}`
- Verified Status Codes: 200, 201, 204, 400, 401, 403, 404, 409, 422.

---

## 4. SQLite Schema & Concurrency PRAGMAs (`docs/recon/ledger-schema.md`)
- Driver: `modernc.org/sqlite` (Pure Go, `CGO_ENABLED=0`)
- Required PRAGMA settings:
  ```sql
  PRAGMA journal_mode = WAL;
  PRAGMA busy_timeout = 5000;
  PRAGMA synchronous = NORMAL;
  PRAGMA foreign_keys = ON;
  PRAGMA cache_size = -64000;
  PRAGMA temp_store = MEMORY;
  ```
- Mutex / Transaction Strategy: `BEGIN IMMEDIATE` + Application-level write serialization (`sync.Mutex`).
- Non-negative balance constraint: `CHECK (balance >= 0)` + `UPDATE accounts SET balance = balance - :amount WHERE user_id = :id AND balance >= :amount`.
- Invariant: Balanced double-entry postings $\sum_{p \in T.\text{postings}} p.\text{amount} = 0$.

---

## 5. Master BAND Room Prompt (`docs/recon/stage-1-room-prompt.md`)
- Directs `@architect` to coordinate `@developer` and `@qa-auditor` without writing production code.
- Fully self-contained with explicit references to API contract and SQLite ledger schema.
- Enforces strict dark-factory execution with zero human steering.
