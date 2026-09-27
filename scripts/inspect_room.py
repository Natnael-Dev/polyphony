import json

with open("room-export.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

messages = raw.get("data", [])
messages.sort(key=lambda m: m.get("inserted_at", ""))

for i in range(min(15, len(messages))):
    m = messages[i]
    sender = m.get("sender_name") or "System"
    ts = m.get("inserted_at", "")[:19]
    print(f"=== Message {i+1} | {ts} | {sender} ===")
    print(m.get("content", ""))
    print("-" * 60)
