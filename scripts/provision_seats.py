#!/usr/bin/env python3
"""
Provision BAND Platform Seats for Polyphony Dark Factory.

Deletes any leftover test agents (Tom, Jerry, etc.) and registers
the 3 official Polyphony seats:
- polyphony-architect
- polyphony-developer
- polyphony-qa

Descriptions and mandates are 100% generic to adhere to Dark Factory rules.
Credentials are saved locally to secrets.json (gitignored).
"""

import json
import os
import sys
import urllib.error
import urllib.request

BAND_BASE_URL = os.environ.get("BAND_BASE_URL", "https://app.band.ai").rstrip("/")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
DEFAULT_USER_KEY = "band_u_1790462199_Z-2ei3dRRTzYmViTyE6NUEmrGVbrO9Bb"

SEATS = [
    {
        "name": "polyphony-architect",
        "description": "System Architect and Coordinator for autonomous dark factory engineering band."
    },
    {
        "name": "polyphony-developer",
        "description": "Software Engineer and Implementer for zero-egress containerized services."
    },
    {
        "name": "polyphony-qa",
        "description": "QA Auditor and Verification Sentinel for adversarial verification and state invariants."
    }
]

def make_request(url: str, method: str = "GET", data: dict | None = None, api_key: str = "") -> dict:
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

def list_agents(user_api_key: str) -> list[dict]:
    url = f"{BAND_BASE_URL}/api/v1/me/agents"
    res = make_request(url, method="GET", api_key=user_api_key)
    return res.get("data", [])

def delete_agent(agent_id: str, user_api_key: str) -> None:
    url = f"{BAND_BASE_URL}/api/v1/me/agents/{agent_id}"
    make_request(url, method="DELETE", api_key=user_api_key)

def register_agent(name: str, description: str, user_api_key: str) -> dict:
    url = f"{BAND_BASE_URL}/api/v1/me/agents/register"
    payload = {
        "agent": {
            "name": name,
            "description": description
        }
    }
    return make_request(url, method="POST", data=payload, api_key=user_api_key)

def main():
    user_api_key = os.environ.get("BAND_USER_API_KEY", "").strip() or DEFAULT_USER_KEY
    if not user_api_key:
        print("ERROR: BAND_USER_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Connecting to BAND platform ({BAND_BASE_URL})...")
    existing_agents = list_agents(user_api_key)
    print(f"Found {len(existing_agents)} existing agent(s).")
    
    # 1. Clean up old test agents or previously registered seats
    target_names = {s["name"] for s in SEATS} | {"Tom", "Jerry"}
    for agent in existing_agents:
        a_id = agent.get("id")
        a_name = agent.get("name")
        if a_name in target_names:
            print(f"Deleting agent: {a_name} ({a_id})...")
            try:
                delete_agent(a_id, user_api_key)
                print(f"  Successfully deleted {a_name}.")
            except Exception as e:
                print(f"  Warning: failed to delete {a_name}: {e}", file=sys.stderr)
                
    # 2. Provision new seats
    secrets = {}
    print("\nProvisioning official Polyphony seats...")
    for seat in SEATS:
        name = seat["name"]
        desc = seat["description"]
        print(f"Registering seat '{name}'...")
        res = register_agent(name, desc, user_api_key)
        data = res.get("data", {})
        agent_data = data.get("agent", {})
        credentials = data.get("credentials", {})
        agent_id = agent_data.get("id")
        api_key = credentials.get("api_key") or res.get("api_key")
        if not agent_id or not api_key:
            raise RuntimeError(f"Unexpected response registering {name}: {res}")
        secrets[name] = {
            "agent_id": agent_id,
            "api_key": api_key,
            "name": name,
            "description": desc
        }
        print(f"  Registered {name} -> Agent ID: {agent_id}")
        
    # 3. Write to secrets.json
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    secrets_path = os.path.join(workspace_dir, "secrets.json")
    with open(secrets_path, "w", encoding="utf-8") as f:
        json.dump(secrets, f, indent=2)
    print(f"\nSaved credentials to {secrets_path} (gitignored).")
    
    # 4. Verify registered agents
    print("\nVerifying registered agents on platform...")
    current_agents = list_agents(user_api_key)
    names = [a.get("name") for a in current_agents]
    print(f"Current active agents on BAND account: {names}")
    for seat in SEATS:
        assert seat["name"] in names, f"Seat {seat['name']} not found in active list!"
    print("All 3 Polyphony seats verified active and healthy!")

if __name__ == "__main__":
    main()
