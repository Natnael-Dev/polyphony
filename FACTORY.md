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
| `@architect` | System Architect & Coordinator | Codex / OpenCode | GPT-5.6 / Gemini 3.8 Flash | Ingests stage specs, defines schema contracts, establishes invariant rules, dispatches work to `@developer`, accepts/rejects stage certificates. Does NOT write production code. |
| `@developer` | Software Engineer & Implementer | Codex / OpenCode | GPT-5.6 / Gemini 3.8 Flash | Implements Go service logic, pure-Go SQLite persistence, Dockerfile packaging, and unit tests. Remediates defects flagged by `@qa-auditor`. Does NOT self-certify. |
| `@qa-auditor` | QA Auditor & Verification Sentinel | Codex / OpenCode | GPT-5.6 / Gemini 3.8 Flash | Independent verification sentinel. Executes zero-egress container tests, harness checks, fuzzing, and concurrency stress checks. Issues pass/fail certificates. Does NOT write production code. |

---

## 2. Design Rationale & Technology Stack

### 2.1 Track Selection: Pocketful (Venmo Clone)
We chose the **pocketful** track because peer-to-peer payment ledgers require absolute mathematical conservation laws. Double-entry bookkeeping and balance invariants provide clear, deterministic oracles for automated QA auditing.

### 2.2 Core Stack: Go 1.24+ & Pure SQLite
- **Zero-Egress Container Runtime**: The service compiles to a single static binary (`CGO_ENABLED=0`) inside an alpine/scratch container.
- **Persistence**: Embedded SQLite via `modernc.org/sqlite` (pure Go transpilation) with WAL mode, `busy_timeout=5000`, and `synchronous=NORMAL`.
- **Concurrency & Invariants**: Application-level write serialization with strict balance conservation ($Total_{credits} == Total_{debits}$).
- **Frontend Architecture (Stage 2+)**: Server-side rendered HTML templates with Vanilla JS and embedded Tailwind CSS, eliminating external runtime assets and Node build fragility.

---

## 3. Cost & Performance Metrics

| Metric | Target | Measured / Estimated |
|---|---|---|
| Stage 1 Container Boot Time | < 1.0s | ~200ms |
| Memory Footprint | < 256 MiB | ~18 MiB (well below 2 GiB limit) |
| Binary Size | < 20 MiB | ~12 MiB static ELF binary |
| Network Calls in Container | 0 | 0 (`--network none` enforced) |
| Agent Turn Latency | < 30s | ~8s per turn on Codex/Gemini |

---

## 4. Self-Healing & Defect Remediation Loop

The factory features an adversarial closed-loop recovery protocol:
1. When `@qa-auditor` detects any harness failure, assertion mismatch, or race condition, it halts stage acceptance.
2. It compiles an actionable Defect Certificate containing reproduction commands, error logs, and failing invariant traces.
3. `@developer` ingests the Defect Certificate, produces a surgical fix, and commits with conventional commit semantics.
4. `@qa-auditor` re-audits the exact new revision until 100% test pass is achieved.
