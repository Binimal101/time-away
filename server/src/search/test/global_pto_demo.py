#!/usr/bin/env python3
"""
Demo script showing how to use the global PTO map functionality.

This script demonstrates:
1. How to save PTO requests to the global database
2. How to retrieve global PTO maps
3. How to use global PTO in scheduling functions
4. How to manage PTO through the database layer
"""

from datetime import date, timedelta, datetime
from typing import Dict, List

from src.search.pto_tools import (
    get_global_pto_map, save_pto_request, delete_pto_request,
    can_approve_pto_strict, get_current_month_schedule, 
    get_effective_pto_map
)
from src.db.helper_functions import (
    get_all_organization_departments, get_people_from_department, 
    get_all_tasks_from_department
)
from src.search._search import PlanStore


def demo_basic_global_pto():
    """Demonstrate basic global PTO operations."""
    print("=== Basic Global PTO Operations ===")
    
    # 1. Save some PTO requests to the global database
    print("1. Saving PTO requests...")
    person_id = "emp_001"
    pto_dates = [
        date.today() + timedelta(days=7),
        date.today() + timedelta(days=8),
        date.today() + timedelta(days=14)
    ]
    
    success = save_pto_request(person_id, pto_dates, status="approved")  # type: ignore
    print(f"   Saved PTO for {person_id}: {success}")
    
    # Save another person's PTO
    person_id_2 = "emp_002"
    pto_dates_2 = [
        date.today() + timedelta(days=10),
        date.today() + timedelta(days=11)
    ]
    success_2 = save_pto_request(person_id_2, pto_dates_2, status="approved")  # type: ignore
    print(f"   Saved PTO for {person_id_2}: {success_2}")
    
    # 2. Retrieve global PTO map
    print("\n2. Retrieving global PTO map...")
    start_date = date.today()
    end_date = date.today() + timedelta(days=30)
    
    global_pto = get_global_pto_map(start_date, end_date)
    print("   Global PTO Map:")
    for pto_date, person_ids in global_pto.items():
        print(f"     {pto_date}: {person_ids}")
    
    return global_pto


def demo_effective_pto_map():
    """Demonstrate combining global PTO with additional PTO."""
    print("\n=== Effective PTO Map (Global + Additional) ===")
    
    # Additional PTO beyond what's in the global database
    additional_pto = {
        date.today() + timedelta(days=5): ["emp_003"],
        date.today() + timedelta(days=15): ["emp_001", "emp_004"]  # emp_001 has additional day
    }
    
    print("1. Additional PTO being considered:", additional_pto)
    
    # Get effective PTO map (combines global + additional)
    start_date = date.today()
    end_date = date.today() + timedelta(days=30)
    
    # Convert to expected format
    additional_pto_formatted = {
        d.isoformat(): person_ids for d, person_ids in additional_pto.items()
    }
    
    effective_pto = get_effective_pto_map(start_date, end_date, additional_pto_formatted)  # type: ignore
    
    print("2. Effective PTO Map (Global + Additional):")
    for pto_date, person_ids in effective_pto.items():
        print(f"   {pto_date}: {person_ids}")


def demo_scheduling_with_global_pto():
    """Demonstrate using global PTO in scheduling functions."""
    print("\n=== Scheduling with Global PTO ===")
    
    try:
        # Get current month schedule using global PTO
        now_epoch = int(datetime.now().timestamp())
        
        # Create a simple PlanStore for the demo
        store = PlanStore()
        
        print("1. Generating current month schedule with global PTO...")
        schedule = get_current_month_schedule(
            store=store,
            now_epoch=now_epoch,
            pto_map=None,  # No additional PTO beyond global
            use_global_pto=True  # Use global PTO database
        )
        
        print(f"   Schedule generated for {schedule['year']}-{schedule['month']:02d}")
        print(f"   Total assignments: {len(schedule['assignments'])}")
        print(f"   Unsatisfied days: {len(schedule['unsatisfied'])}")
        
        if schedule['unsatisfied']:
            print("   Unsatisfied days:")
            for unsat in schedule['unsatisfied'][:3]:  # Show first 3
                print(f"     {unsat['date']}: {unsat['deficits']}")
                
    except Exception as e:
        print(f"   Error in scheduling demo: {e}")
        print("   (This is expected if database is not set up)")


def demo_pto_approval_with_global():
    """Demonstrate PTO approval considering global PTO baseline."""
    print("\n=== PTO Approval with Global Baseline ===")
    
    try:
        # Try to approve new PTO for someone
        person_id = "emp_005"
        candidate_pto_days = [
            date.today() + timedelta(days=12),
            date.today() + timedelta(days=13)
        ]
        
        # Get some people and tasks for the demo
        departments = get_all_organization_departments()
        if departments:
            dept = departments[0]
            people = get_people_from_department(dept)
            
            start_date = min(candidate_pto_days)
            end_date = max(candidate_pto_days)
            tasks = get_all_tasks_from_department(dept, start_date, end_date)
            
            if people and tasks:
                print(f"1. Checking PTO approval for {person_id}")
                print(f"   Candidate days: {[d.isoformat() for d in candidate_pto_days]}")
                
                # Create a simple store
                store = PlanStore()
                now_epoch = int(datetime.now().timestamp())
                
                feasible, result = can_approve_pto_strict(
                    person_id=person_id,
                    pto_days=candidate_pto_days,  # type: ignore
                    people=people,  # type: ignore
                    tasks=tasks,  # type: ignore
                    now_epoch=now_epoch,
                    base_store=store,
                    baseline_pto_map=None,  # Will use global PTO automatically
                    use_global_pto=True,    # Enable global PTO integration
                    save_approved_pto=True  # Automatically save if approved
                )
                
                print(f"   Feasible: {feasible}")
                print(f"   PTO saved to global: {result.get('pto_saved_to_global', False)}")
                
                if not feasible:
                    print(f"   Unsatisfied requirements: {len(result['unsatisfied'])}")
            else:
                print("   No people or tasks found for demo")
        else:
            print("   No departments found for demo")
            
    except Exception as e:
        print(f"   Error in approval demo: {e}")
        print("   (This is expected if database is not set up)")


def demo_cleanup():
    """Clean up demo PTO entries."""
    print("\n=== Cleanup Demo PTO ===")
    
    # Remove the demo PTO entries
    test_people = ["emp_001", "emp_002"]
    
    for person_id in test_people:
        pto_dates = [
            date.today() + timedelta(days=i) 
            for i in range(7, 16)  # Remove days 7-15
        ]
        success = delete_pto_request(person_id, pto_dates)  # type: ignore
        print(f"Cleaned up PTO for {person_id}: {success}")


def main():
    """Run all demos."""
    print("Global PTO System Demo")
    print("=" * 50)
    
    try:
        # Run demos
        demo_basic_global_pto()
        demo_effective_pto_map()
        demo_scheduling_with_global_pto()
        demo_pto_approval_with_global()
        
        # Cleanup
        demo_cleanup()
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        print("Make sure your MongoDB connection is configured in .env")
        print("and that the collections exist.")
    
    print("\n" + "=" * 50)
    print("Demo complete!")


if __name__ == "__main__":
    main()