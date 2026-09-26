# Phase 0.75 Evidence: BAND Integration & Local Adapters

## 1. BAND Adapter Suite
Created in `band/`:
- `band/run_architect.py`: Adapter for `@architect` seat.
- `band/run_developer.py`: Adapter for `@developer` seat.
- `band/run_qa_auditor.py`: Adapter for `@qa-auditor` seat.
- Configured with `approval_mode="auto_accept"` and `turn_timeout_s=900`.

## 2. OpenCode Configuration
Created `band/opencode-config.json`:
- Configured OpenCode local gateway to route agent calls to Gemini 3.8 Flash.

## 3. Human Runbook
Updated `BAND_RUNBOOK.md` with:
- Step-by-step instructions for Windows PowerShell and WSL2.
- Screen recording guidance for BAND Desktop.
- Zero-intervention dark factory execution rules.
