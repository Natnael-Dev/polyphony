# BAND Room Master Orchestration Prompt: Stage 1

## Prompt Overview
This document contains the exact master task prompt to be pasted into the **BAND Desktop** room to initiate autonomous execution of **Stage 1 (Pocketful Track)**. 

In strict adherence to the Dark Factory Hackathon rules, this prompt is the **sole human interaction** with the band. It directs `@architect` to coordinate the seat topology without writing application code directly, enlists `@developer` for Go implementation and containerization, and commands `@qa-auditor` to conduct independent adversarial verification.

---

## Master Task Prompt Text

*(Copy and paste the text block below directly into the BAND Desktop room session)*

```text
@architect You are the System Architect and Coordinator for our autonomous software engineering band.

### CHALLENGE & STAGE
- Track: Pocketful (Venmo-style wallet and double-entry ledger)
- Stage: Stage 1 — Core Payments, Settlements, and Idempotent Ledger API
- Target Workspace: ./stage-1/
- Execution Mode: Pure Dark Factory (Zero Human Intervention). Do not request human confirmation, steering, or approvals.

### CORE SEAT MANDATES & FACTORY TOPOLOGY
You must orchestrate the team and enforce strict separation of duties. Under no circumstances should you implement production code directly:
1. @architect (You): Ingest specifications, prepare self-contained interface and transaction briefs, ensure @developer and @qa-auditor are present in this room, delegate tasks, supervise verification loops, and publish the final stage completion report.
2. @developer: Implement the production Go service, compile static zero-egress binaries, implement the database transaction logic, build Docker containers, run local tests, and report atomic Git commits.
3. @qa-auditor: Independently inspect the committed revision, verify container startup and execution under `--network none`, run the Stage 1 test harness, execute concurrency burst tests, verify monetary conservation, and report either structured defect rejections or an audit certificate.

### INPUT SPECIFICATIONS & RECON BLUEPRINTS
You must incorporate and pass down the full requirements from our Phase 0.5 discovery blueprints:
1. API Contract Specification:
   Read and enforce: docs/recon/api-contract.md
   Every endpoint must match the exact REST paths, request/response JSON bodies, RFC 3339 timestamps, and standardized error envelopes:
   {"error": {"code": "<error_code>", "message": "<human readable>"}}
   Key endpoints:
   - GET /health (200 {"status": "ok"})
   - POST /_test/reset (204 No Content, resets fixture, validates non-negative balances)
   - GET /_test/export & POST /_test/import (atomically exports and restores state)
   - POST /auth/signup & POST /auth/login (derives handles, hashes passwords)
   - GET /me (returns authenticated wallet balance)
   - POST /payments (idempotent, atomic debit/credit, verbatim notes, public/private visibility)
   - POST /requests, POST /requests/{id}/pay, /decline, /cancel, GET /requests (filter by direction/status)
   - POST /splits (equal split algorithm with remainder to first participants)
   - GET /activity (feed visibility contract)
   - POST /settlements (operator-only atomic multi-transfer batch, 1..32 transfers, net affordability)

2. SQLite Ledger Schema & Concurrency Configuration:
   Read and enforce: docs/recon/ledger-schema.md
   - Pure-Go driver: modernc.org/sqlite (CGO_ENABLED=0).
   - PRAGMAs: journal_mode=WAL, busy_timeout=5000, synchronous=NORMAL, foreign_keys=ON, cache_size=-64000, temp_store=MEMORY.
   - Concurrency serialization: Use `BEGIN IMMEDIATE` or an application-level write mutex to guarantee single-writer serialization without SQLITE_BUSY deadlocks.
   - Invariants:
     a) CHECK (balance >= 0) on accounts table.
     b) Atomic UPDATE: `UPDATE accounts SET balance = balance - :amount WHERE user_id = :id AND balance >= :amount`.
     c) Double-entry transactions: Every payment and transfer creates balanced postings where sum(amount) == 0.
     d) Total system wallet balance always equals seeded fixture total.

### OPERATIONAL SEQUENCE
1. Room Preparation: Verify that @developer and @qa-auditor are participants in this room.
2. Briefing & Delegation: Post a comprehensive, self-contained implementation brief to @developer containing all endpoint contracts, schema DDL, error codes, and Docker zero-egress constraints. Never instruct seats to "read the room" or use pointers.
3. Implementation: @developer replaces the temporary health skeleton in `./stage-1/` with the full production Go service, verifies static Docker build, runs internal tests, commits changes cleanly, and posts the Git revision hash tagging @qa-auditor and @architect.
4. Independent Audit: @qa-auditor pulls the revision, builds the container, executes `docker run --network none`, executes the automated test suite, tests 10 concurrent payments on a single wallet (confirming 1 succeeds with 201, 9 fail with 409 insufficient_funds, zero 500 errors), and checks state conservation.
5. Defect Remediation: If @qa-auditor finds any test failure or schema discrepancy, @qa-auditor posts the failure log and reproduction command back to @developer. @developer must diagnose, commit a fix, and request re-audit.
6. Stage Certification: When @qa-auditor issues a clean Audit Certificate confirming 100% compliance, post the final Stage 1 outcome summary to the room.

Begin now by preparing the implementation assignment for @developer.
```

---

## 2. Key Guardrails & Anti-Pattern Defenses

This prompt explicitly guards against common dark-factory failure modes:
1. **Architect Overreach Prevention**: Mandates that `@architect` coordinates rather than writing Go files directly.
2. **Generic Mandate Compliance**: The task prompt holds all track-specific vocabulary (`/payments`, `/settlements`, `insufficient_funds`), ensuring `mandates/*.md` remain 100% generic.
3. **No-Steering Rule**: Pre-defines the self-healing rejection protocol between `@qa-auditor` and `@developer` so that failures are resolved without prompting the human.
4. **Isolated Zero-Egress Enforcement**: Explicitly orders verification under `docker run --network none` to prevent disqualified runtime network fetches.
