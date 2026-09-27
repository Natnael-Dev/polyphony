# Evidence Pack: Phase 1.2 — T1 Workspace Triage & T2 Wake-Semantics Recon

## 1. Task 1: Workspace Triage Findings

### Compilation Output (`cd stage-1; go build ./...`):
```text
stage1
# stage1
.\api.go:127:11: cannot use 2nd function result (value of interface type error) as *apiError value in multiple assignment: need type assertion
.\api.go:146:12: cannot use 2nd function result (value of interface type error) as *apiError value in multiple assignment: need type assertion
.\api.go:147:10: cannot use 2nd function result (value of interface type error) as *apiError value in multiple assignment: need type assertion
.\api.go:150:10: cannot use 2nd function result (value of interface type error) as *apiError value in multiple assignment: need type assertion
.\api.go:156:9: cannot use tx.Commit() (value of interface type error) as *apiError value in assignment: need type assertion
.\api.go:175:6: cannot use a.db.QueryRow("SELECT id,display_name,password_hash FROM users WHERE lower(email)=lower(?)", in.Email).Scan(&id, &display, &hash) (value of interface type error) as *apiError value in assignment: need type assertion
.\api.go:182:12: cannot use 2nd function result (value of interface type error) as *apiError value in multiple assignment: need type assertion
.\testdata.go:72:11: cannot use 2nd function result (value of interface type error) as *apiError value in multiple assignment: need type assertion
.\testdata.go:78:9: cannot use clear(tx) (value of interface type error) as *apiError value in assignment: need type assertion
.\testdata.go:83:9: cannot use 2nd function result (value of interface type error) as *apiError value in multiple assignment: need type assertion
.\testdata.go:83:9: too many errors
```

### Triage Decision:
Per the prompt's decision rule (*"If it does not compile -> git checkout -- stage-1/ to restore the clean skeleton"*), the uncompilable partial files were removed via `git restore stage-1/main.go` and `git clean -fd stage-1/`. The workspace has been restored to the proven, compilable Phase 0 health skeleton.
Recorded in `DECISIONS.md` under ADR-011.
Committed as `chore(stage-1): triage partial work from timed-out run` (`0ff01c3`).

---

## 2. Task 2: BAND SDK Wake-Semantics Recon

### Source Code Inspection:
We conducted a forensic examination of the `band-sdk` runtime in `tom-jerry-agents/.venv/Lib/site-packages/band/`:
1. **Server-Side Message Ingestion**:
   In `band/platform/message_lifecycle.py` and `band/runtime/tools/agent.py`:
   - Polling / WebSocket delivery invokes `rest.agent_api_messages.get_agent_next_message(chat_id=room_id)`.
   - The platform endpoint authoritatively gates actionable messages with query `sender_id == agent_id OR mentions agent_id`.
   - If an incoming message in the room does not explicitly `@mention` the agent's ID or handle, `/next` returns HTTP 204 No Content.
2. **Local Client Routing (`band_sdk_core`)**:
   - `band_sdk_core.evaluate_delivery_event` routes inbound messages.
   - Self-messages are discarded (`is_self_echo`).
   - Non-matching messages with 204 from `/next` trigger `OneShotStatus.NO_PENDING`.
3. **Absence of `wake_on_all` / `respond_to_all`**:
   - There is no client-side adapter configuration flag (`respond_to_all`, `subscribe_all_messages`, or error-wake hook) on `CodexAdapterConfig` or `Agent`.
   - Server-level events without `@mentions` (such as timeout notices: `"Codex turn timed out after 180.0s"`) are treated as unaddressed events and do not wake other agents.

### Architectural Conclusion:
Because `wake-on-all` is unsupported at the platform level, **chunk sizing (~5 minutes per brief) and mandatory `@polyphony-architect` completion handoffs are the sole and definitive timeout insurance.**
If each chunk is bounded, the Developer will never hit a timeout and will always complete its turn with an explicit `@mention` to the Architect.
