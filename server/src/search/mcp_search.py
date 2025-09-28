import os
import datetime, calendar
from typing import Union, List, Dict, Any, Tuple, Set, Optional

import google.generativeai as genai
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from server.src.db.connect import get_db, get_all_collections
from server.src.search._search import HorizonSchedulerPTO, HorizonSchedule
from server.src import _TZ, logger

#TODO database abstractions 
get_all_organization_departments = lambda: [None,] * 6
get_people_from_organization = lambda org: [None] * 6
get_all_tasks_from_organization = lambda org, start_date, end_date: [None] * 6

cache_schedule = lambda org, month, year, schedule: None
load_cached_schedule = lambda org, month, year: None

#start to generate a bunch of schedule data for a organization

def build_full_month_schedule_with_pto(month_date: datetime.date, pto_map: Optional[Dict[datetime.date, Set[str]]]):
    """Builds a monthly schedule with PTO (Paid Time Off) considerations. FULL month for entire org, all departments."""
    depts = get_all_organization_departments()

    for dept in depts:
        people = get_people_from_organization(dept)
        tasks = get_all_tasks_from_organization(dept, first, last)
        build_month_schedule_with_pto_from_items(people, tasks, month_date, pto_map)

def build_month_schedule_with_pto_from_items(people: List[object], tasks: List[object], month_date: datetime.date, pto_map: Optional[Dict[datetime.date, Set[str]]]):
    """Builds a monthly schedule with PTO (Paid Time Off) considerations FROM people and task lists.

    Args:
        people (List[object]): _description_
        tasks (List[object]): _description_
        month_date (datetime.date): _description_
        pto_map (Optional[Dict[datetime.date, Set[str]]]): _description_

    Returns:
        _type_: _description_
    """
    first = month_date.replace(day=1)
    last = (first + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    span = (last - first).days + 1
    return HorizonSchedulerPTO(people, tasks, first, span, int(datetime.datetime.now(tz=_TZ).timestamp()), allow_future=True, pto_map=pto_map).build() # type: ignore 

def get_all_connections_from_database() -> Dict[str, Any]:
    """Get all connections from the database."""
    mongodb_client = get_db()
    collections = mongodb_client.list_collection_names()
    db = {}
    for collection in collections:
        db[collection]= mongodb_client[collection]
    return db
    
def get_people_from_department(db: Dict[str, Any], department: str) -> List[Dict[str, Any]]:
    """Get people from the department with validation and distinct results.
    
    Args:
        db: Database connections dictionary
        department: Department name to filter by
        
    Returns:
        List of distinct user profiles from the department
    """
    if 'user_profile' not in db:
        logger.warning("user_profile collection not found in database")
        return []
    
    # Check if department exists by looking for any users in that department
    dept_check = db['user_profile'].find_one({"department": department})
    if not dept_check:
        logger.warning(f"Department '{department}' not found in database")
        return []
    
    # Get all distinct user profiles from the department
    # Using distinct to ensure no duplicates
    people_cursor = db['user_profile'].find({"department": department})
    
    # Convert to list and ensure distinct by person_id
    people_list = list(people_cursor)
    seen_ids = set()
    distinct_people = []
    
    for person in people_list:
        person_id = person.get('person_id') or person.get('_id')
        if person_id and person_id not in seen_ids:
            seen_ids.add(person_id)
            distinct_people.append(person)
    
    logger.info(f"Found {len(distinct_people)} distinct people in department '{department}'")
    return distinct_people

def get_all_tasks_from_department(db: Dict[str, Any], department: str) -> List[Dict[str, Any]]:
    """Get all tasks from the department.
    
    Args:
        db: Database connections dictionary
        department: Department name to filter by
        
    Returns:
        List of tasks from the department
    """
    if 'tasks' not in db:
        logger.warning("tasks collection not found in database")
        return []
    
    # Get all tasks from the department
    tasks_cursor = db['tasks'].find({"department": department})
    tasks_list = list(tasks_cursor)
    
    logger.info(f"Found {len(tasks_list)} tasks in department '{department}'")
    return tasks_list
# ------------------ MCP Server for Gemini ------------------

def _init_gemini() -> None:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv()  # fallback to any .env in parent dirs or CWD
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set in environment")
    genai.configure(api_key=api_key)


def create_mcp_server() -> FastMCP:
    _init_gemini()
    mcp = FastMCP("gemini-mcp")

    def gemini_generate(prompt: str, model: str = "models/gemini-2.5-flash", temperature: float = 0.2) -> str:
        candidates = [
            model,
            "models/gemini-2.5-pro",
            "models/gemini-2.5-flash",
            "models/gemini-flash-latest",
            "models/gemini-pro-latest",
        ]
        last_err = None
        for m in candidates:
            try:
                llm = genai.GenerativeModel(m)
                resp = llm.generate_content(prompt, generation_config={"temperature": temperature})
                return resp.text or ""
            except Exception as e:
                last_err = e
                continue
        # As a final fallback, pick the first model supporting generateContent
        try:
            for mdl in genai.list_models():
                if getattr(mdl, "supported_generation_methods", None) and "generateContent" in mdl.supported_generation_methods:
                    llm = genai.GenerativeModel(mdl.name)
                    resp = llm.generate_content(prompt, generation_config={"temperature": temperature})
                    return resp.text or ""
        except Exception:
            pass
        raise last_err or RuntimeError("No supported Gemini model found for generate_content")

    # expose helper for external callers
    mcp.gemini_generate = gemini_generate  # type: ignore[attr-defined]

    @mcp.tool()
    def gemini_chat(prompt: str, model: str = "gemini-1.5-pro-latest", temperature: float = 0.2) -> Dict[str, str]:
        """Send a prompt to Gemini and return the response text.

        Args:
            prompt: The user prompt.
            model: Gemini model name.
            temperature: Sampling temperature.
        """
        return {"text": gemini_generate(prompt, model=model, temperature=temperature)}

    @mcp.tool()
    def month_schedule_example() -> Dict[str, object]:
        """Build example month schedule to verify scheduler wiring."""
        people = []
        tasks = []
        hs = build_month_schedule_with_pto_from_items(people, tasks, datetime.date.today(), pto_map={})
        return {"feasible": hs.feasible, "days": len(hs.days)}

    @mcp.tool()
    def mcp_read_connections_db() -> Dict[str, object]:
        """Read connections from the database."""
        db = get_all_connections_from_database()
        return {"connections": list(db.keys())}

    @mcp.tool()
    def get_people_by_department(department: str) -> Dict[str, object]:
        """Get all people from a specific department (READ-ONLY).
        
        Args:
            department: The department name to query
            
        Returns:
            Dictionary with people list and metadata
        """
        try:
            db = get_all_connections_from_database()
            people = get_people_from_department(db, department)
            return {
                "department": department,
                "people_count": len(people),
                "people": people,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error getting people from department {department}: {e}")
            return {
                "department": department,
                "people_count": 0,
                "people": [],
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def get_tasks_by_department(department: str) -> Dict[str, object]:
        """Get all tasks from a specific department (READ-ONLY).
        
        Args:
            department: The department name to query
            
        Returns:
            Dictionary with tasks list and metadata
        """
        try:
            db = get_all_connections_from_database()
            tasks = get_all_tasks_from_department(db, department)
            return {
                "department": department,
                "tasks_count": len(tasks),
                "tasks": tasks,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error getting tasks from department {department}: {e}")
            return {
                "department": department,
                "tasks_count": 0,
                "tasks": [],
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def list_all_departments() -> Dict[str, object]:
        """List all available departments (READ-ONLY).
        
        Returns:
            Dictionary with departments list and metadata
        """
        try:
            db = get_all_connections_from_database()
            if 'user_profile' not in db:
                return {
                    "departments": [],
                    "departments_count": 0,
                    "success": False,
                    "error": "user_profile collection not found"
                }
            
            # Get distinct departments
            departments = db['user_profile'].distinct("department")
            return {
                "departments": departments,
                "departments_count": len(departments),
                "success": True
            }
        except Exception as e:
            logger.error(f"Error listing departments: {e}")
            return {
                "departments": [],
                "departments_count": 0,
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def get_user_profile_by_id(person_id: str) -> Dict[str, object]:
        """Get a specific user profile by ID (READ-ONLY).
        
        Args:
            person_id: The person ID to query
            
        Returns:
            Dictionary with user profile and metadata
        """
        try:
            db = get_all_connections_from_database()
            if 'user_profile' not in db:
                return {
                    "person_id": person_id,
                    "profile": None,
                    "success": False,
                    "error": "user_profile collection not found"
                }
            
            profile = db['user_profile'].find_one({"person_id": person_id})
            if not profile:
                profile = db['user_profile'].find_one({"_id": person_id})
            
            return {
                "person_id": person_id,
                "profile": profile,
                "success": profile is not None
            }
        except Exception as e:
            logger.error(f"Error getting user profile for {person_id}: {e}")
            return {
                "person_id": person_id,
                "profile": None,
                "success": False,
                "error": str(e)
            }

    return mcp


def run_mcp_server() -> None:
    server = create_mcp_server()
    server.run()


if __name__ == "__main__":
    run_mcp_server()

# def fill_month_schedule(today: datetime.date = datetime.date.today()):
#     """TODO check cached dates against last 7 days to pre-populate preworked_in_last_7 for employees.

#     Generates a schedule for all departments in an organization for the month specified at a generic date (in the month).
#     Defaults to filling current month
#     """
#     first_of_month = today.replace(day=1)
#     last_day = calendar.monthrange(today.year, today.month)[1]
#     last_of_month = today.replace(day=last_day)

#     month_span_days = (last_of_month - first_of_month).days + 1

#     #goes dept for dept, gets all people and tasks, generates a schedule for the MONTH (monthview generator)
#     for dept in get_all_organization_departments():  
#         if not load_cached_schedule(dept, today.month, today.year):
#             schedule = abstract_output(HorizonScheduler(
#                 people=get_people_from_organization(dept), # type: ignore
#                 tasks=get_all_tasks_from_organization(dept, first_of_month, last_of_month), # type: ignore
#                 start_day=first_of_month,
#                 span_days=month_span_days,
#                 current_ts=today, # type: ignore
#                 allow_future=True
#             ))

#             cache_schedule(dept, today.month, today.year, schedule)