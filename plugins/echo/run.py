import json
import sys

payload = json.load(sys.stdin)
args = payload.get("args") or {}
print(json.dumps({"ok": True, "echo": args}, ensure_ascii=False))
