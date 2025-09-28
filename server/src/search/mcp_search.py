import os
import datetime, calendar
from typing import Union, List, Dict, Any, Tuple, Set, Optional

import google.generativeai as genai
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

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