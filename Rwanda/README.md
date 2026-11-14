# The Drying Floor at Karongi

Fix for the broken LangGraph state machine in `graph.py` (task_rwanda).

## Problem

The graph models a coffee drying floor:

```
receive_batch -> inspect_batch -> (not ready) -> dry_batch -> inspect_batch -> ...
                               -> (ready)     -> grade_batch -> END
```

Every batch looped between `inspect_batch` and `dry_batch` forever and never reached
`grade_batch`, so the run exhausted the step budget (`GraphRecursionError`).

## Root cause

`inspect_batch` computed `ready` (whether moisture is inside 10.5-12.5 %) but never
returned it. The `approved` field in the state therefore stayed `False`, and
`route_after_inspection`, which routes on `state["approved"]`, always sent the batch
back to `dry_batch`.

In LangGraph a node only changes state through the dict it returns; a local variable
has no effect.

## Fix

One line in `inspect_batch`:

```python
# before
return {"inspections": state["inspections"] + 1}

# after
return {"inspections": state["inspections"] + 1, "approved": ready}
```

Nothing else was changed: the constants, `BatchState`, `receive_batch`, `dry_batch`,
`grade_batch`, `route_after_inspection`, `build_graph` and `initial_state` are identical
to `graph_reference.py`, and no `batch_id` is special-cased.

## Files

- `graph.py` - corrected graph
- `run_log.txt` - output of `evaluation_script.py`
