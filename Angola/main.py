"""Find the trace item responsible for the incorrect answer and write answer.txt."""
import json
import sys
from collections import defaultdict
from datetime import datetime

path = sys.argv[1] if len(sys.argv) > 1 else "test-input.json"
with open(path, encoding="utf-8") as f:
    events = json.load(f)["events"]

ts = lambda s: datetime.fromisoformat(s)

runs = defaultdict(list)
for e in events:
    runs[e["run_id"]].append(e)

candidates = []
for run_id, evs in runs.items():
    # memory items that were actually injected into the context
    injected = [e["item"] for e in evs
                if e["event"] == "memory.result" and e.get("injected_into_context")]
    # ids that really reached the model request
    in_request = {m.get("source_id")
                  for e in evs if e["event"] == "llm.request"
                  for m in e["messages"] if m["role"] == "memory"}
    # the live tool status for this run
    tool = next((e["result"] for e in evs if e["event"] == "tool.result"), None)
    asked_at = ts(next(e for e in evs if e["event"] == "assistant.prompt")["timestamp"])

    for item in injected:
        stale = ts(item["valid_until"]) < asked_at           # expired before the question
        conflicts = tool is not None and (
            ("NOT been restored" in item["text"] or "ongoing" in item["text"])
            and tool["status"] == "RESTORED")
        if item["source_id"] in in_request and stale and conflicts:
            candidates.append((run_id, item["source_id"]))

if len(candidates) != 1:
    sys.exit(f"Expected exactly one candidate, got: {candidates}")

run_id, source_id = candidates[0]
print(f"Run: {run_id}\nResponsible item: {source_id}")
with open("answer.txt", "w", encoding="utf-8") as f:
    f.write(source_id + "\n")
