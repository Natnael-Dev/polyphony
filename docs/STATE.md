# Project State: WeAreDevelopers x BAND (Dark Factory)

## Current Status
- **Phase**: Phase 1.0 — Automated Seat Provisioning, GitHub Push & Master Launch.
- **Timestamp**: 2026-09-27.
- **Git State**: Clean, Phase 0 through 0.9 committed. ADR-008 documented.
- **Recon & Setup Artifacts**:
  - `docs/recon/github-setup.md`: Step-by-step public GitHub repository initialization & push guide.
  - `docs/recon/windows-opencode-gemini.md`: Windows OpenCode install, Gemini API mapping, and direct SDK adapter alternative.
  - `BAND_RUNBOOK.md`: Updated with Windows PowerShell syntax, OpenCode setup, and direct connection tip.
  - `PROGRESS.md`, `SESSION_LOG.md`, `DECISIONS.md`: Project memory files auto-updated (.gitignore protected).
  - Adapter Audit: `codex-cli` v0.155.1 verified healthy and authenticated.

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
- **Agent Execution Engine**: CodexAdapter via verified `codex-cli` (ADR-008); `approval_mode="auto_accept"` and `turn_timeout_s=900`. Direct Gemini SDK adapter as fallback.

## Next Steps
1. Provision the 3 official Polyphony seats (`polyphony-architect`, `polyphony-developer`, `polyphony-qa`) via BAND REST API (`scripts/provision_seats.py`) and write `secrets.json`.
2. Create and push public GitHub repository `polyphony` via GitHub MCP.
3. Implement `launch_polyphony.py` master orchestrator.
4. Auto-update memory and evidence.
