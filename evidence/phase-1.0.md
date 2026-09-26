# Phase 1.0 Evidence: Automated Seat Provisioning, GitHub Push & Launch Script

## 1. Automated BAND Seat Provisioning Output
Command: `python scripts/provision_seats.py`
Raw unedited output:
```text
Connecting to BAND platform (https://app.band.ai)...
Found 1 existing agent(s).
Deleting agent: polyphony-architect (b8054d53-dc3b-44b2-8ad6-2305a5a8bf8f)...
  Successfully deleted polyphony-architect.

Provisioning official Polyphony seats...
Registering seat 'polyphony-architect'...
  Registered polyphony-architect -> Agent ID: 70f5fa39-5c94-4005-b0a7-8c71f6224699
Registering seat 'polyphony-developer'...
  Registered polyphony-developer -> Agent ID: 84a7a969-dbe0-45a2-a739-73557e8036bb
Registering seat 'polyphony-qa'...
  Registered polyphony-qa -> Agent ID: b485e453-998a-42dc-8b34-e3c9f4bdc142

Saved credentials to C:\Users\HP\dev\WeAreDevelopers x BAND\secrets.json (gitignored).
Saved agent config to C:\Users\HP\dev\WeAreDevelopers x BAND\agent_config.yaml (gitignored).

Verifying registered agents on platform...
Current active agents on BAND account: ['polyphony-qa', 'polyphony-developer', 'polyphony-architect']
All 3 Polyphony seats verified active and healthy!
```

---

## 2. Public GitHub Repository Setup & Push
Created via GitHub MCP tool `create_repository`:
- Repository URL: `https://github.com/Natnael-Dev/polyphony`
- Visibility: **Public** (clean-room compliance)
- Full name: `Natnael-Dev/polyphony`
- Description: `WeAreDevelopers x BAND Dark Factory AI Hackathon - Pocketful Track`

Latest commits on remote `main`:
```text
4e7921c feat: update seat adapters to use CodexAdapter with mandate integration
6bb8ce9 feat: add launch_polyphony.py and generate_agent_config.py
35e2de3 docs: add api contract and ledger schema blueprints
c777451 docs: add setup, reconnaissance, and prompt documentation
18fbd63 feat: add band adapters and stage skeletons
8c63d8c docs: add phase evidence reports
a02362a feat: add FACTORY report and agent mandates
f4bbfea chore: add .gitignore
74683b4 chore: initialize AGENTS.md in polyphony repository
```

---

## 3. Master Launch Script Preflight Verification
Command: `python launch_polyphony.py --preflight-only`
Raw unedited output:
```text
================================================================================
🔍 RUNNING POLYPHONY DARK FACTORY PREFLIGHT CHECKS
================================================================================
  [+] Python Interpreter: C:\Users\HP\dev\WeAreDevelopers x BAND\tom-jerry-agents\.venv\Scripts\python.exe
  [+] Codex CLI: C:\Users\HP\AppData\Roaming\npm\codex.CMD
  [+] Seat Credentials: 3 seats verified in secrets.json
  [+] Agent Config: C:\Users\HP\dev\WeAreDevelopers x BAND\agent_config.yaml present
  [+] Master Task Prompt: C:\Users\HP\dev\WeAreDevelopers x BAND\docs\recon\stage-1-room-prompt.md present
  [+] BAND Platform Key: Authenticated (Key ID: band_u_17904...)

✅ PREFLIGHT SUCCESSFUL: ALL SYSTEMS ARMED AND READY.
================================================================================
```

---

## 4. Human Launch Instructions

The Dark Factory is fully automated and armed. The human operator only needs to:

1. **Launch BAND Desktop App**: Ensure BAND Desktop is open on screen.
2. **Start Screen Recording**: Position your screen recorder over BAND Desktop (recording the live agent conversation is mandatory for submission).
3. **Execute Master Launcher**:
   ```powershell
   python launch_polyphony.py
   ```
4. **Arm & Trigger**:
   - `launch_polyphony.py` will automatically start the 3 agent seats (`@polyphony-architect`, `@polyphony-developer`, `@polyphony-qa`), create the `stage-1-pocketful` room, and invite all seats.
   - When the recording countdown appears, confirm screen recording is running and press **ENTER**.
   - The script dispatches the Stage 1 Master Task Prompt.
5. **Sit Back (Zero Intervention)**:
   - Do **NOT** type in the room or steer the agents.
   - Watch the agents design the Go architecture, build the zero-egress container, test double-entry invariants, and issue the audit certificate autonomously.
