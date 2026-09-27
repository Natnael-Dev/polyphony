# Project State: WeAreDevelopers x BAND (Dark Factory)

## Current Status
- **Phase**: Phase 1.2 Complete — Ready to Launch Stage 1 (Chunked Orchestration Architecture).
- **Timestamp**: 2026-09-27.
- **Git State**: Clean, tracking main branch on https://github.com/Natnael-Dev/polyphony.
- **Seats & Orchestration**:
  - 3 Official Polyphony seats active on BAND: `polyphony-architect`, `polyphony-developer`, `polyphony-qa`.
  - Seat credentials persisted in local `secrets.json` and `agent_config.yaml`.
  - Master launcher `launch_polyphony.py` armed with chunked room prompt (`docs/recon/stage-1-room-prompt.md`).
  - Preflight validated via `scripts/safety_preflight.ps1`.
  - Evidence compiled in `evidence/phase-1.2.md`.

## Key Milestone Deadlines
- **Kickoff**: Sat, Sep 26, 2026, 09:00 PDT / 16:00 UTC / 18:00 CEST.
- **Submission Deadline**: Mon, Oct 05, 2026, 23:59 PDT / Tue Oct 06, 06:59 UTC / 08:59 CEST.

## Current Architecture Decisions
- **Official Kickoff Repo Cloned**: Available in `hackathon_docs/dark-factory-wearedevs/` (ignored by git).
- **Available Specs**: All 4 stage specifications for both `pocketful` and `tablekeeper` are locally available.
- **Available Test Harness**: Shipped test suites and `python -m harness` CLI ready for local iteration.
- **Selected Track**: `pocketful` (Venmo-style wallet/payments app with double-entry ledger invariants).
- **Core Agent Topology**: 3 seats in BAND Desktop (`@architect`, `@developer`, `@qa-auditor`).
- **Persistence & Concurrency**: Pure Go `modernc.org/sqlite` with WAL mode, `busy_timeout=5000`, `synchronous=NORMAL`, and application-level write serialization.
- **Agent Execution Engine**: CodexAdapter via verified `codex-cli` (ADR-008); `approval_mode="auto_accept"` and `turn_timeout_s=900`.
- **Chunked Pipeline**: 6 sequential briefs (B1–B6) with atomic checkpoint commits, interim ledger Q-gate after B2, and final zero-egress QA certification gate (ADR-012).

## Next Steps
1. Human runs `powershell -ExecutionPolicy Bypass -File scripts\safety_preflight.ps1` to verify git hygiene.
2. Human runs `python launch_polyphony.py`.
3. Human starts screen recording on BAND Desktop window and presses ENTER.
4. Band executes B1–B6 autonomously, passing through dual QA gates to produce QA Audit Certificate.
5. Export room session via `harness export-room` and run verification suite.
