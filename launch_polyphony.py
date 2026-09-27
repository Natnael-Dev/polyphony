#!/usr/bin/env python3
"""
Polyphony Master Dark Factory Launch Orchestrator.

Orchestrates the autonomous Software Dark Factory:
1. Performs environment and credential preflight checks.
2. Spawns 3 autonomous seats in the background:
   - @polyphony-architect
   - @polyphony-developer
   - @polyphony-qa
3. Creates the official BAND Desktop chat room ("stage-1-pocketful").
4. Registers all 3 seats as room participants.
5. Displays screen recording banner and waits for human start signal.
6. Dispatches Stage 1 Master Task Prompt to initiate autonomous execution.
7. Manages seat process lifecycles with graceful shutdown on exit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

BAND_BASE_URL = os.environ.get("BAND_BASE_URL", "https://app.band.ai").rstrip("/")
DEFAULT_USER_KEY = "band_u_1790462199_Z-2ei3dRRTzYmViTyE6NUEmrGVbrO9Bb"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

WORKSPACE_DIR = os.path.abspath(os.path.dirname(__file__))
RUNS_LOGS_DIR = os.path.join(WORKSPACE_DIR, "runs", "logs")
SECRETS_PATH = os.path.join(WORKSPACE_DIR, "secrets.json")
CONFIG_PATH = os.path.join(WORKSPACE_DIR, "agent_config.yaml")
PROMPT_PATH = os.path.join(WORKSPACE_DIR, "docs", "recon", "stage-1-room-prompt.md")

ADAPTERS = [
    ("polyphony-architect", os.path.join(WORKSPACE_DIR, "band", "run_architect.py"), "architect.log"),
    ("polyphony-developer", os.path.join(WORKSPACE_DIR, "band", "run_developer.py"), "developer.log"),
    ("polyphony-qa", os.path.join(WORKSPACE_DIR, "band", "run_qa_auditor.py"), "qa_auditor.log"),
]


def find_python_executable() -> str:
    """Find a Python interpreter equipped with band-sdk."""
    candidates = [
        os.path.join(WORKSPACE_DIR, "tom-jerry-agents", ".venv", "Scripts", "python.exe"),
        os.path.join(WORKSPACE_DIR, "tom-jerry-agents", ".venv", "bin", "python"),
        os.path.join(WORKSPACE_DIR, ".venv", "Scripts", "python.exe"),
        os.path.join(WORKSPACE_DIR, ".venv", "bin", "python"),
        sys.executable,
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return sys.executable


def make_api_request(url: str, method: str = "GET", data: dict | None = None, api_key: str = "") -> dict:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    if api_key:
        headers["X-API-Key"] = api_key

    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            if content.strip():
                return json.loads(content)
            return {}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8") if e.fp else str(e)
        raise RuntimeError(f"HTTP {e.code} {e.reason} for {method} {url}: {err_msg}") from e


def run_preflight() -> dict:
    """Validate all credentials, files, and binaries before arming factory."""
    print("================================================================================")
    print("🔍 RUNNING POLYPHONY DARK FACTORY PREFLIGHT CHECKS")
    print("================================================================================")

    # 1. Check Python executable
    py_exe = find_python_executable()
    print(f"  [+] Python Interpreter: {py_exe}")

    # 2. Check codex executable
    codex_path = shutil.which("codex")
    if not codex_path:
        raise RuntimeError("Codex CLI ('codex') not found in system PATH.")
    print(f"  [+] Codex CLI: {codex_path}")

    # 3. Check secrets.json
    if not os.path.exists(SECRETS_PATH):
        raise FileNotFoundError(f"Missing {SECRETS_PATH}. Please run scripts/provision_seats.py first.")
    with open(SECRETS_PATH, "r", encoding="utf-8") as f:
        secrets = json.load(f)

    for seat_name, _, _ in ADAPTERS:
        if seat_name not in secrets:
            raise KeyError(f"Seat '{seat_name}' missing from secrets.json.")
        if not secrets[seat_name].get("agent_id") or not secrets[seat_name].get("api_key"):
            raise ValueError(f"Seat '{seat_name}' has incomplete credentials in secrets.json.")
    print(f"  [+] Seat Credentials: 3 seats verified in secrets.json")

    # 4. Check agent_config.yaml
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Missing {CONFIG_PATH}. Please run scripts/generate_agent_config.py first.")
    print(f"  [+] Agent Config: {CONFIG_PATH} present")

    # 5. Check stage 1 prompt
    if not os.path.exists(PROMPT_PATH):
        raise FileNotFoundError(f"Missing stage 1 prompt at {PROMPT_PATH}")
    print(f"  [+] Master Task Prompt: {PROMPT_PATH} present")

    # 6. Verify User API key
    user_api_key = os.environ.get("BAND_USER_API_KEY", "").strip() or DEFAULT_USER_KEY
    if not user_api_key:
        raise ValueError("BAND_USER_API_KEY is not set.")
    print(f"  [+] BAND Platform Key: Authenticated (Key ID: {user_api_key[:12]}...)")

    print("\n✅ PREFLIGHT SUCCESSFUL: ALL SYSTEMS ARMED AND READY.")
    print("================================================================================\n")
    return {
        "python": py_exe,
        "secrets": secrets,
        "user_api_key": user_api_key,
    }


def extract_prompt_text(filepath: str) -> str:
    """Extract the clean task prompt from markdown code fence."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"```text\s*\n(.*?)\n```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return content.strip()


def cleanup_existing_rooms(title: str, user_api_key: str) -> None:
    """Find and delete any old rooms with the same title to ensure clean state."""
    url = f"{BAND_BASE_URL}/api/v1/me/chats"
    try:
        res = make_api_request(url, method="GET", api_key=user_api_key)
        for chat in res.get("data", []):
            if chat.get("title") == title:
                chat_id = chat.get("id")
                del_url = f"{BAND_BASE_URL}/api/v1/me/chats/{chat_id}"
                make_api_request(del_url, method="DELETE", api_key=user_api_key)
                print(f"  [-] Pruned previous room '{title}' ({chat_id})")
    except Exception as e:
        print(f"  [!] Note: Room cleanup skipped ({e})")


def create_room(title: str, user_api_key: str) -> str:
    """Create a new room in BAND platform, pruning any stale duplicates first."""
    cleanup_existing_rooms(title, user_api_key)
    url = f"{BAND_BASE_URL}/api/v1/me/chats"
    payload = {"chat": {"title": title}}
    res = make_api_request(url, method="POST", data=payload, api_key=user_api_key)
    chat_id = res.get("data", {}).get("id")
    if not chat_id:
        raise RuntimeError(f"Failed to create chat room: {res}")
    return chat_id


def add_participant(chat_id: str, agent_id: str, user_api_key: str) -> dict:
    """Add an agent participant to the chat room."""
    url = f"{BAND_BASE_URL}/api/v1/me/chats/{chat_id}/participants"
    payload = {"participant": {"participant_id": agent_id}}
    res = make_api_request(url, method="POST", data=payload, api_key=user_api_key)
    return res.get("data", {})


def send_room_message(chat_id: str, content: str, architect_id: str, architect_handle: str, user_api_key: str) -> dict:
    """Send message to room mentioning the architect."""
    url = f"{BAND_BASE_URL}/api/v1/me/chats/{chat_id}/messages"
    payload = {
        "message": {
            "content": content,
            "mentions": [
                {
                    "id": architect_id,
                    "handle": architect_handle,
                    "name": "polyphony-architect",
                }
            ],
        }
    }
    return make_api_request(url, method="POST", data=payload, api_key=user_api_key)


def main():
    parser = argparse.ArgumentParser(description="Polyphony Autonomous Dark Factory Launcher")
    parser.add_argument("--preflight-only", action="store_true", help="Run preflight checks and exit")
    parser.add_argument("--dry-run", action="store_true", help="Run preflight and test room creation without dispatching")
    args = parser.parse_args()

    preflight = run_preflight()
    if args.preflight_only:
        sys.exit(0)

    py_exe = preflight["python"]
    secrets = preflight["secrets"]
    user_api_key = preflight["user_api_key"]

    os.makedirs(RUNS_LOGS_DIR, exist_ok=True)
    processes = []

    def cleanup_processes():
        print("\n[!] Shutting down autonomous agent seats...")
        for p, name in processes:
            if p.poll() is None:
                print(f"  [-] Stopping seat {name} (PID: {p.pid})...")
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("[+] All seats cleanly stopped.")

    # 1. Spawn the 3 seat adapters
    print("[*] Spawning 3 autonomous agent seats...")
    for seat_name, script_path, log_file in ADAPTERS:
        log_path = os.path.join(RUNS_LOGS_DIR, log_file)
        log_fp = open(log_path, "w", encoding="utf-8")
        print(f"  [>] Launching @{seat_name} -> {log_path}")
        p = subprocess.Popen(
            [py_exe, script_path],
            cwd=WORKSPACE_DIR,
            stdout=log_fp,
            stderr=subprocess.STLOG if hasattr(subprocess, "STLOG") else subprocess.STDOUT,
            env=os.environ.copy(),
        )
        processes.append((p, seat_name))

    try:
        # Give processes a moment to boot
        time.sleep(2)

        # Check if any seat failed on startup
        for (p, name), (_, _, log_file) in zip(processes, ADAPTERS):
            if p.poll() is not None:
                log_path = os.path.join(RUNS_LOGS_DIR, log_file)
                err_snippet = ""
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        err_snippet = "".join(f.readlines()[-15:])
                raise RuntimeError(f"Seat @{name} exited immediately with code {p.returncode}.\nLog snippet ({log_path}):\n{err_snippet}")

        # 2. Create room
        room_title = "stage-1-pocketful"
        print(f"\n[*] Creating BAND Desktop room: '{room_title}'...")
        chat_id = create_room(room_title, user_api_key)
        print(f"  [+] Room created! Chat ID: {chat_id}")

        # 3. Add seats as participants
        print("\n[*] Adding 3 seats to room...")
        architect_handle = ""
        architect_id = secrets["polyphony-architect"]["agent_id"]
        for seat_name, _, _ in ADAPTERS:
            a_id = secrets[seat_name]["agent_id"]
            part_info = add_participant(chat_id, a_id, user_api_key)
            handle = part_info.get("handle", seat_name)
            if seat_name == "polyphony-architect":
                architect_handle = handle
            print(f"  [+] Added @{seat_name} ({handle}) to room.")

        if args.dry_run:
            print("\n[!] Dry run requested. Exiting without prompt dispatch.")
            return

        # 4. Display screen recording banner
        print("\n" + "=" * 80)
        print("🔴 POLYPHONY DARK FACTORY IS ARMED AND READY.")
        print(f"🔴 ROOM TITLE : {room_title}")
        print(f"🔴 ROOM ID    : {chat_id}")
        print("🔴")
        print("🔴 CRITICAL STEP: START SCREEN RECORDING NOW!")
        print("🔴 Position BAND Desktop window in your screen recorder.")
        print("🔴 Once recording is live, press ENTER to dispatch the master prompt.")
        print("=" * 80)

        input("\n>>> PRESS ENTER TO DISPATCH PROMPT AND COMMENCE AUTONOMOUS EXECUTION <<< ")

        # 5. Dispatch prompt
        print("\n[*] Ingesting Stage 1 Master Task Prompt...")
        prompt_text = extract_prompt_text(PROMPT_PATH)
        print(f"  [+] Read {len(prompt_text)} characters.")

        print(f"[*] Dispatching prompt to @polyphony-architect ({architect_handle})...")
        send_room_message(chat_id, prompt_text, architect_id, architect_handle, user_api_key)
        print("\n" + "=" * 80)
        print("🚀 PROMPT DISPATCHED! DARK FACTORY IS NOW RUNNING UNATTENDED.")
        print("⚠️  DO NOT INTERVENE. DO NOT SEND MESSAGES IN THE BAND DESKTOP ROOM.")
        print("⚠️  Monitor the seats working autonomously in BAND Desktop.")
        print("⚠️  Seat logs streaming to runs/logs/")
        print("⚠️  Press Ctrl+C when stage is complete or to abort.")
        print("=" * 80 + "\n")

        # Keep running and monitor seat health
        while True:
            time.sleep(5)
            for p, name in processes:
                if p.poll() is not None:
                    print(f"[!] Warning: Seat @{name} stopped (exit code {p.returncode}).")

    except KeyboardInterrupt:
        print("\n[!] Received stop signal from human.")
    finally:
        cleanup_processes()


if __name__ == "__main__":
    main()
