import json

with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

lines = ["# Auto-generated Polyphony BAND seat credentials (gitignored)\n"]
for s_name, creds in secrets.items():
    lines.append(f"{s_name}:\n")
    lines.append(f'  agent_id: "{creds["agent_id"]}"\n')
    lines.append(f'  api_key: "{creds["api_key"]}"\n\n')

with open("agent_config.yaml", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Generated agent_config.yaml successfully.")
