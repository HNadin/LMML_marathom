# The Waterline Replay

Finds the trace item responsible for the incorrect water-service answer in an agent-trace export (`agent-trace/1.2`).

## Problem

The assistant was asked whether water was restored in Kilamba Sector 4. In run `incident-01` it answered "No", although the live status tool returned `RESTORED`. The goal is to find the `source_id` of the trace item that caused this.

## Approach

Events are grouped by `run_id`. For each run, the script looks for a memory item that satisfies all of the following:

1. It was injected into the context (`memory.result` with `injected_into_context: true`).
2. It actually reached the model (a `memory` message with the same `source_id` appears in `llm.request`).
3. It was stale: its `valid_until` is earlier than the time of the question.
4. It contradicts the live tool result: the text says the outage is ongoing or "NOT been restored", while `get_service_status` returned `RESTORED`.

Exactly one candidate must match; otherwise the script exits with an error.

The traces back this up. The control run and the `replay-no-memory` run (same config and seed, memory disabled) both answer correctly from the live status alone.

