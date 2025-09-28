import datetime
from typing import List
from src.db.connect import get_dept_collection, get_user_profile_collection, get_tasks_collection
from src.search._search import Person, Task
from datetime import datetime as dt


def get_all_organization_departments() -> List[str]:
    """
    Retrieves all department names from the database.
    
    Returns:
        List[str]: List of department names
    """
    dept_collection = get_dept_collection()
    departments = dept_collection.find({}, {"name": 1, "_id": 0})
    return [dept["name"] for dept in departments]


def get_people_from_organization(org: str) -> List[Person]:
    """
    Retrieves all people from a specific organization/department.
    
    Args:
        org (str): Department/organization name
        
    Returns:
        List[Person]: List of Person objects with skills and work history
    """
    user_collection = get_user_profile_collection()
    users = user_collection.find({"department": org})
    
    people = []
    for user in users:
        person = Person(
            person_id=str(user["_id"]),
            skills=set(user["skills"]),
            preworked_in_last_7=0  # Default to 0 as we don't track this in the schema yet
        )
        people.append(person)
    
    return people


def get_all_tasks_from_organization(org: str, start_date: datetime.date, end_date: datetime.date) -> List[Task]:
    """
    Retrieves all tasks for an organization within a date range.
    
    Note: Current task schema doesn't have organization field, so we filter by date range only.
    In a real implementation, tasks would be linked to departments.
    
    Args:
        org (str): Department/organization name (currently unused due to schema limitation)
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
    # In a real implementation, we'd add organization field to tasks
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