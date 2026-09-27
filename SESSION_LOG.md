# Session Log — Engineering Memory

## Session 1: Phase 0 — Skeleton, Mandates & Zero-Egress Container
- **Date**: 2026-09-26
- **Objective**: Establish repo structure, configure offline Docker, craft 3 generic mandates.
- **Actions Taken**:
  - Initialized git repository with `.gitignore` excluding `hackathon_docs/`, binaries, and DBs.
  - Authored 3 generic mandates (`mandates/architect.md`, `mandates/developer.md`, `mandates/qa-auditor.md`). Verified that mandates contain zero track-specific vocabulary (`harness/vocabulary.py`).
  - Implemented Go 1.24+ module in `stage-1/` with pure-Go SQLite driver (`modernc.org/sqlite`).
  - Authored multi-stage `Dockerfile` and verified clean build and boot with `docker run --network none`.
  - Authored initial `FACTORY.md` detailing seat topology and design rationale.
- **Commits**:
  - `7ac84ae` chore: initial repo setup and dark factory folder structure
  - `979764f` feat: add generic agent mandates for dark factory band
  - `5c53b76` feat(stage-1): init go module with pure-go sqlite and health endpoint
  - `6238a92` ci(stage-1): add zero-egress multi-stage dockerfile
  - `bc5e574` docs: initialize FACTORY.md with seat setup and rationale

---

## Session 2: Phase 0.5 — Deep Recon & Open Source Research
- **Date**: 2026-09-27
- **Objective**: Reverse-engineer harness tests, design SQLite ledger schema, draft master orchestration prompt.
- **Actions Taken**:
  - Ingested official kickoff repository and test suites in `hackathon_docs/dark-factory-wearedevs/pocketful/test/`.
  - Reverse-engineered exact API contract: 16 REST endpoints, 5 idempotent write paths, RFC 3339 timestamps, integer minor units, and standardized `{"error": {"code": ...}}` envelope in `docs/recon/api-contract.md`.
  - Researched Go + SQLite concurrency best practices using `modernc.org/sqlite`. Configured WAL mode (`journal_mode=WAL`), `busy_timeout=5000`, `synchronous=NORMAL`, and write mutex serialization.
  - Designed double-entry ledger schema DDL with non-negative balance checks (`CHECK (balance >= 0)`) and balanced postings ($\sum \text{amount} = 0$) in `docs/recon/ledger-schema.md`.
  - Authored the master BAND Desktop room orchestration prompt in `docs/recon/stage-1-room-prompt.md`.
  - Updated `FACTORY.md` with double-entry ledger architecture and QA verification commands.
- **Commits**:
  - `6ab5a40` docs(recon): map pocketful harness API contract
  - `49195ad` docs(recon): define optimal sqlite double-entry schema
  - `87e8fb1` docs(recon): draft stage-1 band room orchestration prompt
  - `f58014e` docs: update FACTORY.md with phase 0.5 research findings
  - `f3d69b1` docs: update STATE.md for phase 0.5 completion
  - `13d71f0` docs: add phase 0.5 evidence pack

---

## Session 3: Phase 0.75 — BAND Integration Prep & Project Memory
- **Date**: 2026-09-27
- **Objective**: Implement local BAND SDK adapters, OpenCode gateway configuration, and human launch runbook.
- **Actions Taken**:
  - Authored three Python BAND SDK adapters (`band/run_architect.py`, `band/run_developer.py`, `band/run_qa_auditor.py`) with `approval_mode="auto_accept"` and `turn_timeout_s=900`.
  - Created OpenCode configuration `band/opencode-config.json` supporting Google Gemini.
  - Authored step-by-step launch manual `BAND_RUNBOOK.md` detailing room creation, participant onboarding, screen recording, and execution rules.
  - Established project memory files (`PROGRESS.md`, `SESSION_LOG.md`, `DECISIONS.md`) protected under `.gitignore`.
- **Commits**:
  - `491cb60` chore: add project memory and progress tracking files
  - `9001255` feat(band): add BAND SDK adapter scripts for 3 seats
  - `730cb0a` feat(band): add opencode gateway configuration
  - `942b147` docs: add BAND Desktop human runbook
  - `7939b70` docs: update progress for phase 0.75 completion
  - `5dc80cc` docs: add phase 0.75 evidence pack

---

## Session 4: Phase 0.9 — Public Repo Setup & Windows/Gemini API Recon
- **Date**: 2026-09-27
- **Objective**: Author GitHub public repository initialization guide, verify Windows OpenCode setup, and document Gemini API key mapping.
- **Actions Taken**:
  - Authored `docs/recon/github-setup.md` with exact PowerShell commands to create and push the public GitHub repo.
  - Performed deep recon of OpenCode installation on Windows (via npm/package managers) and mapped Gemini API key in `docs/recon/windows-opencode-gemini.md`.
  - Discovered native alternative: BAND SDK `OpenAISDKAdapter` can connect directly to Gemini's OpenAI-compatible endpoint without local OpenCode gateway.
  - Updated `BAND_RUNBOOK.md` with Windows PowerShell syntax, config file locations, and direct SDK connection instructions.
  - Auto-updated project memory files (`PROGRESS.md`, `SESSION_LOG.md`, `DECISIONS.md`).

---

## Session 5: Phase 1.0 — Automated Seat Provisioning, GitHub Push & Master Launch Script
- **Date**: 2026-09-27
- **Objective**: Clean up test agents, provision official Polyphony seats on Band.ai, publish repository to GitHub via GitHub MCP, and build master launch automation.
- **Actions Taken**:
  - Implemented `scripts/provision_seats.py` using Band.ai REST API: deleted old Tom & Jerry test agents, registered 3 official seats (`polyphony-architect`, `polyphony-developer`, `polyphony-qa`) with 100% generic mandates and descriptions.
  - Saved credentials locally to `secrets.json` and generated `agent_config.yaml` (.gitignore protected).
  - Created public GitHub repository `Natnael-Dev/polyphony` via GitHub MCP `create_repository`.
  - Pushed all tracked repository files and commits to `main` on GitHub via GitHub MCP `push_files`.
  - Updated seat adapters in `band/` (`run_architect.py`, `run_developer.py`, `run_qa_auditor.py`) to integrate `CodexAdapter` with mandate injection.
  - Engineered master launcher `launch_polyphony.py`: performs preflight validation, spawns seat adapters, creates room `stage-1-pocketful`, binds seats as participants, presents screen recording banner, and dispatches Stage 1 prompt upon user input.
  - Verified preflight execution with zero errors (`python launch_polyphony.py --preflight-only`).
  - Compiled comprehensive evidence report in `evidence/phase-1.0.md`.

---

## Session 6: Adapter Runtime Hardening (Logging & Auto-Accept)
- **Date**: 2026-09-27
- **Objective**: Fix seat process immediate exit caused by missing optional JSON logging dependency; enforce fully autonomous tool execution.
- **Actions Taken**:
  - Identified root cause in `runs/logs/architect.log`: `BandConfigError: Logging style <LoggingStyle.JSON: 'json'> requires optional dependency 'python-json-logger>=3.1.0'`.
  - Updated `band/run_architect.py`, `band/run_developer.py`, and `band/run_qa_auditor.py` to use `style="standard"` logging.
  - Set `approval_mode="auto_accept"` in `CodexAdapterConfig` across all 3 seat adapters to prevent interactive tool-approval freezes.
  - Verified concurrent startup of all 3 seats locally with 0 exit codes.
  - Committed changes and pushed to GitHub repository `Natnael-Dev/polyphony` via GitHub MCP.
  - Clarified UI state: BAND Desktop yellow banner `Claude Code integration is not installed` is benign since Polyphony operates on `codex-cli`.

---

## Session 7: Stage 1 Post-Run Audit Prep & Turn Timeout Extension
- **Date**: 2026-09-27
- **Objective**: Audit autonomous Stage 1 run, verify screen recording, inspect room logs and developer code generation, prepare evidence pack.
- **Actions Taken**:
  - Located video screen recording on Desktop at `C:\Users\HP\OneDrive\Desktop\Recordings\stage-1-run.mp4` (464.1 MB).
  - Inspected initial run: diagnosed that agents were sandboxed in an empty `.band-workspaces/` read-only folder; fixed by setting `workspace_for_room=lambda _: WORKSPACE_DIR` and `sandbox="danger-full-access"`.
  - Audited second run (Room `a443031a-73aa-43a6-9834-26a8e7c96711`, 11 messages): confirmed `@polyphony-developer` actively entered `stage-1/` and began authoring `main.go` with core ledger primitives (`move`, double-entry postings, payments, requests).
  - Identified turn timeout interruption: developer hit default 180s turn limit (`Codex turn timed out after 180.0s`) before finishing the remaining endpoints.
  - Configured `turn_timeout_s=900` across all 3 seat adapters to afford 15 minutes for complete multi-endpoint compilation and container verification.
  - Generated comprehensive evidence report in `evidence/stage-1-audit-prep.md`.
  - Updated `PROGRESS.md` and `SESSION_LOG.md`.

---

## Session 8: Phase 1.2 — Chunked Orchestration Architecture & Timeout Insurance
- **Date**: 2026-09-27
- **Objective**: Triage timed-out Run #2 partial work, investigate BAND SDK wake semantics, eliminate monolithic timeout risk via sequential chunked orchestration prompt.
- **Actions Taken**:
  - T1: Inspected `stage-1/` partial artifacts left by Run #2. Discovered 11+ compile errors (`cannot use error as *apiError`). Executed clean reset to Phase 0 baseline via `git restore stage-1/main.go` and `git clean -fd stage-1/`. Verified clean compilation. Recorded ADR-011. Committed `0ff01c3`.
  - T2: Conducted deep forensic analysis of `band-sdk` v3.2.0 and `band_sdk_core`. Proved server-authoritative message delivery on `/next` requires explicit `@mentions`. Timeout notices are unaddressed and never wake peer agents. Concluded chunk sizing (<5 min) + mandatory `@polyphony-architect` completion handshakes are the sole viable timeout insurance. Documented in `evidence/phase-1.2.md`. Committed `e8f5adc`.
  - T3: Completely rewrote master room prompt (`docs/recon/stage-1-room-prompt.md`) into 6 sequential, timeout-proof briefs (B1–B6) with atomic checkpoint commits (`feat(stage-1): ...`), an interim ledger Q-gate after B2, and a final zero-egress QA certification gate. Committed `3c18eff`.
  - T4: Updated `FACTORY.md` with Section 2.6 documenting the chunked architecture, appended ADR-012 to `DECISIONS.md`, and refreshed `PROGRESS.md`, `SESSION_LOG.md`, and `docs/STATE.md`.

---

## Session 9: Phase 1.2.1 — Pre-Launch Patch & Recordings Inventory
- **Date**: 2026-09-27
- **Objective**: Constrain B4 prompt scope to Stage 1 contract, push latest commits to remote `main`, organize screen recordings inventory.
- **Actions Taken**:
  - P1: Bounded Brief 4 in `docs/recon/stage-1-room-prompt.md` to the exact Stage 1 API contract defined in `docs/recon/api-contract.md`. Added explicit boundary: *"Batch/operator settlement extensions beyond this contract are OUT OF SCOPE for Stage 1 and deferred to Stage 4."* Committed: `051a1f0` `docs(recon): bound B4 to stage-1 contract scope`.
  - P2: Synchronized and pushed `origin/main` (`git push`). Verified `git ls-remote origin main` (`051a1f0...`) matches local `git rev-parse HEAD` (`051a1f0...`).
  - P3: Desktop Screen Recordings Inventory:
    - **Run 1 (Sandbox Fault, 30.7 MB)**: `C:\Users\HP\OneDrive\Desktop\Recordings\run1-sandbox-fault.mp4`
    - **Run 2 (Monolithic Timeout, 486.6 MB)**: `C:\Users\HP\OneDrive\Desktop\Recordings\run2-monolithic-timeout.mp4`
    - Both recordings remain strictly outside git tracking on Desktop per hackathon repository hygiene.
