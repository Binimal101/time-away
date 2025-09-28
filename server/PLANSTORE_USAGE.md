# PlanStore Usage Guide for FastAPI Server

## How to get/use a PlanStore in your FastAPI server

The `get_current_month_schedule()` function accepts three types for the `store` parameter:
1. `PlanStore` object
2. `dict` object
3. `str` (JSON string)

## Option 1: Empty PlanStore (Fresh Scheduling)
```python
from src.search._search import PlanStore

# Create a fresh, empty PlanStore
store = PlanStore()

# Use it in scheduling
schedule = get_current_month_schedule(
    store=store,
    now_epoch=int(time.time()),
    use_global_pto=True
)
```

## Option 2: PlanStore from JSON String
```python
# If you have a JSON string (from database, client request, etc.)
store_json = '{"person1": ["2024-12-01", "2024-12-02"], "person2": ["2024-12-03"]}'

# Use it directly (the function will parse it)
schedule = get_current_month_schedule(
    store=store_json,  # Pass JSON string directly
    now_epoch=int(time.time()),
    use_global_pto=True
)
```

## Option 3: PlanStore from Dict
```python
import json
from src.search._search import PlanStore

# If you have a dict with plan data
plan_data = {
    "person1": ["2024-12-01", "2024-12-02"],
    "person2": ["2024-12-03", "2024-12-04"]
}

# Convert to PlanStore
store = PlanStore.from_json(json.dumps(plan_data))

# Or use the dict directly (less recommended)
schedule = get_current_month_schedule(
    store=plan_data,  # type: ignore
    now_epoch=int(time.time()),
    use_global_pto=True
)
```

## FastAPI Request Examples

### Client Request - Empty Store (Fresh Schedule)
```json
POST /calendar
{
  "use_global_pto": true,
  "timezone_offset": -8
}
```

### Client Request - With Store JSON
```json
POST /calendar
{
  "store_json": "{\"emp_001\": [\"2024-12-01\"], \"emp_002\": [\"2024-12-02\"]}",
  "use_global_pto": true,
  "additional_pto": {
    "2024-12-15": ["emp_003"]
  }
}
```

### Client Request - With Plan Data
```json
POST /calendar
{
  "plan_data": {
    "emp_001": ["2024-12-01", "2024-12-02"],
    "emp_002": ["2024-12-03"]
  },
  "use_global_pto": true
}
```

## Server-side Implementation

Your FastAPI server now handles all three cases:

```python
@app.post("/calendar", tags=["calendar"])
async def get_calendar(req: CalendarRequest):
    # Option 1: Use provided JSON string (most flexible)
    if req.store_json:
        store = req.store_json
    # Option 2: Create PlanStore from plan_data dict
    elif req.plan_data:
        store = PlanStore.from_json(json.dumps(req.plan_data))
    # Option 3: Create empty PlanStore (fresh scheduling)
    else:
        store = PlanStore()
    
    # Generate schedule with global PTO integration
    schedule_result = get_current_month_schedule(
        store=store,
        now_epoch=int(time.time()),
        pto_map=req.additional_pto,
        tz_offset_hours=req.timezone_offset,
        use_global_pto=req.use_global_pto  # Uses global PTO database
    )
    
    return {"success": True, "schedule": schedule_result}
```

## Global PTO Integration

The key benefit is the `use_global_pto=True` parameter:
- Automatically fetches approved PTO from your MongoDB database
- Combines it with any additional PTO you provide
- No need to manually manage PTO maps across requests
- Consistent scheduling across your entire system

## PlanStore Persistence

If you want to persist PlanStore data between requests:

1. **Get the final state after scheduling:**
```python
# After calling get_current_month_schedule, the store is updated
final_store_json = store.to_json()  # Convert back to JSON

# Save to database, send to client, etc.
```

2. **Use it in subsequent requests:**
```python
# Client sends back the store_json from previous response
# Your server uses it as the starting point for next scheduling
```

This creates a stateful scheduling system where each request builds on the previous scheduling history.