# BAND SDK Adapters for Dark Factory

This directory provides the local BAND SDK adapters that connect our three autonomous seats (`@architect`, `@developer`, `@qa-auditor`) to the BAND Desktop room via a local OpenCode gateway using Google Gemini 3.8 Flash.

---

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the local OpenCode server (in a dedicated terminal):
   ```bash
   opencode serve --hostname=127.0.0.1 --port=4096
   ```

3. Launch each seat adapter in its own terminal:
   - **Terminal 1 (@architect)**:
     ```bash
     python run_architect.py
     ```
   - **Terminal 2 (@developer)**:
     ```bash
     python run_developer.py
     ```
   - **Terminal 3 (@qa-auditor)**:
     ```bash
     python run_qa_auditor.py
     ```

---

## Environment Variables Configuration

Set credentials before running the scripts:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (consumed by OpenCode server) |
| `BAND_AGENT_ID_ARCHITECT` | Agent ID for Architect seat from BAND Desktop console |
| `BAND_API_KEY_ARCHITECT` | Agent API Key for Architect seat |
| `BAND_AGENT_ID_DEVELOPER` | Agent ID for Developer seat from BAND Desktop console |
| `BAND_API_KEY_DEVELOPER` | Agent API Key for Developer seat |
| `BAND_AGENT_ID_QA_AUDITOR` | Agent ID for QA Auditor seat from BAND Desktop console |
| `BAND_API_KEY_QA_AUDITOR` | Agent API Key for QA Auditor seat |
| `OPENCODE_BASE_URL` | OpenCode server endpoint (default: `http://127.0.0.1:4096`) |
| `WORKSPACE_DIR` | Absolute path to the repository root |
