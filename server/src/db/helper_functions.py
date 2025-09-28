import datetime
from typing import List, Dict, Optional, Union
from src.db.connect import get_dept_collection, get_user_profile_collection, get_tasks_collection, get_pto_collection
from src.search._search import Person, Task
from datetime import datetime as dt, date

def get_all_organization_departments() -> List[str]:
    """
    Retrieves all department names from the database.
    
    Returns:
        List[str]: List of department names
    """
    dept_collection = get_dept_collection()
    departments = dept_collection.find({}, {"name": 1, "_id": 0})
    return [dept["name"] for dept in departments]


def get_people_from_department(dept: str) -> List[Person]:
    """
    Retrieves all people from a specific department/department.
    
    Args:
        dept (str): Department/department name
        
    Returns:
        List[Person]: List of Person objects with skills and work history
    """
    user_collection = get_user_profile_collection()
    users = user_collection.find({"department": dept})
    
    people = []
    for user in users:
        person = Person(
            person_id=str(user["_id"]),
            name=user.get("name", "Unnamed"),
            skills=set(user["skills"]),
        )
        people.append(person)
    
    return people

def get_all_tasks_from_department(dept: str, start_date: datetime.date, end_date: datetime.date) -> List[Task]:
    """
    Retrieves all tasks for an department within a date range.
    
    Note: Current task schema doesn't have department field, so we filter by date range only.
    In a real implementation, tasks would be linked to departments.
    
    Args:
        dept (str): Department/department name (currently unused due to schema limitation)
        start_date (datetime.date): Start date for task filtering
        end_date (datetime.date): End date for task filtering
        
    Returns:
        List[Task]: List of Task objects within the date range
    """
    tasks_collection = get_tasks_collection()
    
    # Convert date objects to strings for MongoDB comparison
    start_str = start_date.strftime("%B %d, %Y")
    end_str = end_date.strftime("%B %d, %Y")
    
    # For now, get all tasks and filter by date range
    # In a real implementation, we'd add department field to tasks
    all_tasks = tasks_collection.find({})
    
    filtered_tasks = []
    for task_doc in all_tasks:
        try:
            # Parse the date strings from the database
            task_start = dt.strptime(task_doc["start_date"], "%B %d, %Y").date()
            task_end = dt.strptime(task_doc["end_date"], "%B %d, %Y").date()
            
            # Check if task overlaps with our date range
            if task_start <= end_date and task_end >= start_date:
                # Convert to epoch timestamps for Task object
                start_ts = int(dt.combine(task_start, dt.min.time()).timestamp())
                end_ts = int(dt.combine(task_end, dt.min.time()).timestamp())
                
                task = Task(
                    task_id=str(task_doc["_id"]),
                    required_skills=task_doc["requirements"],
                    start_ts=start_ts,
                    end_ts=end_ts
                )
                filtered_tasks.append(task)
        except (ValueError, KeyError) as e:
            # Skip tasks with invalid date formats or missing fields
            continue
    
    return filtered_tasks


def abstract_output(horizon_scheduler: 'HorizonScheduler') -> dict:
    """
    Processes HorizonScheduler output and returns a structured result.
    
    Args:
        horizon_scheduler: HorizonScheduler instance
        
    Returns:
        dict: Processed schedule data
    """
    schedule = horizon_scheduler.build()
    
    return {
        "feasible": schedule.feasible,
        "violations": schedule.violations,
        "start_date": schedule.start_iso,
        "end_date": schedule.end_iso,
        "timezone": schedule.tz,
        "days_count": len(schedule.days),
        "total_assignments": sum(len(day.assignments) for day in schedule.days)
    }


def get_global_pto_map(start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[Union[date, str], List[str]]:
    """
    Retrieves the global PTO map from the database.
    
    Args:
        start_date: Optional start date to filter PTO requests
        end_date: Optional end date to filter PTO requests
        
    Returns:
        Dict mapping dates to lists of person IDs who are on PTO
    """
    pto_collection = get_pto_collection()
    
    query: Dict[str, Union[str, Dict[str, str]]] = {"status": "approved"}  # Only get approved PTO requests
    
    if start_date or end_date:
        date_filter: Dict[str, str] = {}
        if start_date:
            date_filter["$gte"] = start_date.isoformat()
        if end_date:
            date_filter["$lte"] = end_date.isoformat()
        query["pto_date"] = date_filter
    
    pto_requests = pto_collection.find(query)
    
    pto_map = {}
    for request in pto_requests:
        pto_date = date.fromisoformat(request["pto_date"])
        person_id = str(request["person_id"])
        
        if pto_date not in pto_map:
            pto_map[pto_date] = []
        pto_map[pto_date].append(person_id)
    
    return pto_map


def save_pto_request(person_id: str, pto_dates: List[Union[date, str]], status: str = "approved") -> bool:
    """
    Saves PTO request(s) to the global database.
    
    Args:
        person_id: ID of the person requesting PTO
        pto_dates: List of dates for PTO
        status: Status of the request (approved, pending, denied)
        
    Returns:
        bool: True if saved successfully
    """
    pto_collection = get_pto_collection()
    
    try:
        for pto_date in pto_dates:
            if isinstance(pto_date, str):
                pto_date = date.fromisoformat(pto_date)
                
            document = {
                "person_id": person_id,
                "pto_date": pto_date.isoformat(),
                "status": status,
                "created_at": dt.now(),
                "updated_at": dt.now()
            }
            
            # Use upsert to avoid duplicates
            pto_collection.update_one(
                {"person_id": person_id, "pto_date": pto_date.isoformat()},
                {"$set": document},
                upsert=True
            )
        return True
    except Exception as e:
        print(f"Error saving PTO request: {e}")
        return False


def delete_pto_request(person_id: str, pto_dates: List[Union[date, str]]) -> bool:
    """
    Removes PTO request(s) from the global database.
    
    Args:
        person_id: ID of the person
        pto_dates: List of dates to remove
        
    Returns:
        bool: True if deleted successfully
    """
    pto_collection = get_pto_collection()
    
    try:
        for pto_date in pto_dates:
            if isinstance(pto_date, str):
                pto_date = date.fromisoformat(pto_date)
                
            pto_collection.delete_one({
                "person_id": person_id,
                "pto_date": pto_date.isoformat()
            })
        return True
    except Exception as e:
        print(f"Error deleting PTO request: {e}")
        return False