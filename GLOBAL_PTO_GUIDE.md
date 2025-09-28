# Global PTO Map System

This document explains how to use the newly implemented global PTO (Paid Time Off) map functionality in your scheduling system.

## Overview

The global PTO map system provides a centralized database-backed approach to managing approved PTO requests across your organization. Instead of passing PTO maps manually to each function, the system can automatically fetch and apply globally approved PTO from the database.

## Key Features

1. **Database-Backed Storage**: PTO requests are stored in MongoDB for persistence
2. **Automatic Integration**: Functions can automatically use global PTO without manual parameters
3. **Flexible Merging**: Combine global baseline PTO with additional/temporary PTO
4. **FastMCP Integration**: API endpoints for managing PTO through the MCP protocol
5. **Backward Compatibility**: All existing functionality still works with manual PTO maps

## Database Schema

The system uses a new MongoDB collection `pto_requests` with the following structure:

```javascript
{
  "_id": ObjectId("..."),
  "person_id": "emp_001",
  "pto_date": "2024-12-15",    // ISO date string
  "status": "approved",         // "pending", "approved", "denied"
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

## Core Functions

### Database Functions

Located in `src/db/helper_functions.py`:

```python
# Retrieve global PTO map from database
get_global_pto_map(start_date=None, end_date=None) -> Dict[date, List[str]]

# Save PTO request to database
save_pto_request(person_id, pto_dates, status="approved") -> bool

# Remove PTO request from database  
delete_pto_request(person_id, pto_dates) -> bool
```

### PTO Integration Functions

Located in `src/search/pto_tools.py`:

```python
# Get effective PTO map (global + additional)
get_effective_pto_map(start_date, end_date, additional_pto=None) -> Dict[date, List[str]]
```

## Usage Examples

### 1. Basic Global PTO Operations

```python
from datetime import date, timedelta
from src.search.pto_tools import save_pto_request, get_global_pto_map

# Save approved PTO to global database
person_id = "emp_001"
pto_dates = [date.today() + timedelta(days=7), date.today() + timedelta(days=8)]
success = save_pto_request(person_id, pto_dates, status="approved")

# Retrieve global PTO for date range
global_pto = get_global_pto_map(
    start_date=date.today(),
    end_date=date.today() + timedelta(days=30)
)
print(global_pto)
# Output: {date(2024, 12, 15): ['emp_001'], date(2024, 12, 16): ['emp_001']}
```

### 2. Scheduling with Global PTO

```python
from src.search.pto_tools import get_current_month_schedule
from src.search._search import PlanStore

# Generate monthly schedule automatically using global PTO
schedule = get_current_month_schedule(
    store=PlanStore(),
    now_epoch=int(datetime.now().timestamp()),
    pto_map=None,           # No additional PTO needed
    use_global_pto=True     # Automatically fetch from database
)
```

### 3. PTO Approval with Global Baseline

```python
from src.search.pto_tools import can_approve_pto_strict

# Check if new PTO can be approved, considering existing global PTO
feasible, result = can_approve_pto_strict(
    person_id="emp_002",
    pto_days=["2024-12-20", "2024-12-21"],
    people=people_list,
    tasks=tasks_list,
    now_epoch=now_epoch,
    base_store=plan_store,
    use_global_pto=True,        # Consider existing global PTO
    save_approved_pto=True      # Automatically save if approved
)

if feasible:
    print("PTO approved and saved to global database!")
```

### 4. Combining Global + Additional PTO

```python
from src.search.pto_tools import get_effective_pto_map

# Additional PTO beyond what's in global database
additional_pto = {
    "2024-12-25": ["emp_003"],      # Christmas day
    "2024-12-26": ["emp_001", "emp_004"]  # Day after Christmas
}

# Get combined PTO map
effective_pto = get_effective_pto_map(
    start_date=date(2024, 12, 1),
    end_date=date(2024, 12, 31),
    additional_pto=additional_pto
)
```

## Updated Function Parameters

### Functions with Global PTO Support

All these functions now accept a `use_global_pto: bool = True` parameter:

- `can_approve_pto()`: Added `use_global_pto` parameter
- `can_approve_pto_strict()`: Added `use_global_pto` and `save_approved_pto` parameters  
- `generate_month_view()`: Added `use_global_pto` parameter
- `get_current_month_schedule()`: Added `use_global_pto` parameter

### Backward Compatibility

All existing code continues to work unchanged. To use global PTO features:

```python
# Old way (still works)
can_approve_pto(person_id, pto_days, people, tasks, now_epoch, baseline_pto_map=my_pto_map)

# New way with global PTO
can_approve_pto(person_id, pto_days, people, tasks, now_epoch, use_global_pto=True)

# Disable global PTO and use only manual maps
can_approve_pto(person_id, pto_days, people, tasks, now_epoch, use_global_pto=False, baseline_pto_map=my_pto_map)
```

## FastMCP API Endpoints

If FastMCP is available, these endpoints are automatically registered:

### 1. `approve_pto_request_strict`
- Approves PTO requests with strict checking
- Supports `use_global_pto` and `save_approved_pto` parameters

### 2. `generate_monthly_schedule` 
- Generates monthly schedules using global PTO
- Accepts `use_global_pto` parameter

### 3. `manage_global_pto`
- Manage global PTO database: save, delete, or retrieve PTO entries
- Actions: "save", "delete", "get"

Example FastMCP usage:

```javascript
// Generate monthly schedule with global PTO
{
  "tool": "generate_monthly_schedule",
  "arguments": {
    "store_json": "{}",
    "now_epoch": 1703030400,
    "use_global_pto": true
  }
}

// Manage global PTO
{
  "tool": "manage_global_pto", 
  "arguments": {
    "action": "save",
    "person_id": "emp_001",
    "pto_dates": ["2024-12-25", "2024-12-26"]
  }
}
```

## Benefits

1. **Centralized Management**: All approved PTO is stored in one place
2. **Automatic Integration**: No need to manually pass PTO maps around
3. **Consistency**: All scheduling functions use the same PTO baseline
4. **Audit Trail**: Database provides history and traceability
5. **API Ready**: FastMCP endpoints for external integration
6. **Scalable**: Database storage supports large organizations

## Migration Guide

To migrate existing code to use global PTO:

1. **Database Setup**: Ensure MongoDB connection is configured
2. **Update Function Calls**: Add `use_global_pto=True` to function calls
3. **Populate Global PTO**: Use `save_pto_request()` to populate existing PTO data
4. **Test Integration**: Verify that global PTO is being applied correctly

## Demo Script

Run the demo script to see the global PTO system in action:

```bash
cd server/src/search
python global_pto_demo.py
```

The demo shows:
- Saving PTO to global database
- Retrieving global PTO maps  
- Combining global + additional PTO
- Using global PTO in scheduling
- PTO approval with global baseline

## Error Handling

The system gracefully handles database connectivity issues:

- If the database is unavailable, functions fall back to manual PTO maps
- Warning messages are logged when global PTO cannot be accessed
- All functions continue to work with `use_global_pto=False`

This ensures your scheduling system remains functional even if the database is temporarily unavailable.