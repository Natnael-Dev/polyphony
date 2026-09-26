# Windows OpenCode & Gemini API Deep Recon

## Overview
This document specifies the verified installation commands, configuration files, and authentication mechanics for running the **BAND Desktop $\leftrightarrow$ OpenCode $\leftrightarrow$ Google Gemini** bridge on native **Windows 11 / Windows PowerShell**. It also documents the alternative direct connection method via `OpenAISDKAdapter` that eliminates the OpenCode middleman.

---

## 1. OpenCode Windows Installation Guide

On Windows, the `curl | bash` command will fail in standard Windows PowerShell. Use one of the verified native methods:

### Method 1: Global NPM Install (Recommended for Native Windows)
If Node.js is installed on your Windows system:
```powershell
# In PowerShell (Run as Current User or Administrator)
npm install -g opencode-ai

# Verify installation and PATH registration
opencode --version
```

### Method 2: Windows Package Managers
```powershell
# Using Chocolatey
choco install opencode

# Using Scoop
scoop install opencode
```

### Method 3: WSL2 (If Running in Linux Subsystem)
```bash
# Inside WSL2 Ubuntu bash shell
curl -fsSL https://opencode.ai/install | bash
```

---

## 2. Gemini API Key Configuration in OpenCode

OpenCode stores global configuration at:
`C:\Users\<username>\.config\opencode\opencode.json`

To configure Google Gemini using an API key from [Google AI Studio](https://aistudio.google.com/):

### Option A: Direct Google Provider (`@ai-sdk/google`)
Create or edit `C:\Users\HP\.config\opencode\opencode.json`:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "google": {
      "options": {
        "apiKey": "{env:GEMINI_API_KEY}"
      },
      "models": {
        "gemini-2.5-flash": {
          "name": "Gemini 2.5 Flash"
        },
        "gemini-2.0-flash": {
          "name": "Gemini 2.0 Flash"
        }
      }
    }
  }
}
```

### Option B: OpenAI-Compatible Gateway (`@ai-sdk/openai-compatible`)
Google Gemini provides an official OpenAI-compatible endpoint at `https://generativelanguage.googleapis.com/v1beta/openai/`:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "gemini": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Google Gemini",
      "options": {
        "baseURL": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "apiKey": "{env:GEMINI_API_KEY}"
      },
      "models": {
        "gemini-2.5-flash": {},
        "gemini-2.0-flash": {}
      }
    }
  }
}
```

### Option C: Interactive `/connect`
Inside any terminal running `opencode`:
1. Type `/connect`.
2. Select **Google Gemini**.
3. Paste your `GEMINI_API_KEY` when prompted.

---

## 3. How BAND Python Adapter Bridges to OpenCode

The BAND Python SDK provides `OpencodeAdapter`:
```python
from band.adapters import OpencodeAdapter, OpencodeAdapterConfig

adapter = OpencodeAdapter(
    config=OpencodeAdapterConfig(
        base_url="http://127.0.0.1:4096",
        directory=WORKSPACE_DIR,
        provider_id="gemini",       # Matches provider key in opencode.json
        model_id="gemini-2.5-flash", # Matches model in opencode.json
        approval_mode="auto_accept", # Required for unattended Dark Factory operation
        turn_timeout_s=900,         # 15 minutes per agent turn
    ),
    emit={Emit.TOOL_CALLS, Emit.TASK_EVENTS},
)
```

### Execution Lifecycle:
1. **Room Trigger**: A `@mention` to `@architect`, `@developer`, or `@qa-auditor` in the BAND Desktop room triggers a WebSocket event.
2. **Adapter Proxy**: The adapter translates the message into an HTTP request to `http://127.0.0.1:4096`.
3. **Model Query**: OpenCode injects `$env:GEMINI_API_KEY` and calls the Gemini API.
4. **Execution**: Tool actions (file edits, test runs) execute in `directory` without prompting the user (`approval_mode="auto_accept"`).
5. **Event Emission**: Logs and committed revisions are published back to the room.

---

## 4. Discovery Requirement: Direct Native Gemini Connection (No OpenCode)

> [!TIP]
> **SIMPLER ARCHITECTURAL ALTERNATIVE**:
> The BAND SDK (`band-sdk`) includes a built-in `OpenAISDKAdapter`. Because Google Gemini exposes a full OpenAI-compatible API endpoint, you can connect Gemini **directly** to BAND Desktop without running a local OpenCode server on port 4096.

### Direct Connection Code Pattern:
```python
import os
from band import Agent
from band.adapters import OpenAISDKAdapter

# Direct connection to Google Gemini API
adapter = OpenAISDKAdapter(
    model="gemini-2.5-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_API_KEY"),
    cwd=os.getenv("WORKSPACE_DIR", "c:\\Users\\HP\\dev\\WeAreDevelopers x BAND"),
)

agent = Agent.create(adapter=adapter, agent_id=AGENT_ID, api_key=API_KEY)
```

### Advantages of the Direct Approach:
1. **Zero Intermediate Daemons**: Eliminates the need to start `opencode serve --port 4096` in Terminal 0.
2. **Native Windows Reliability**: Completely avoids localhost port-binding conflicts or Windows firewall popups.
3. **Low Latency**: Direct HTTP/WebSocket streaming from Python to Google's API.
