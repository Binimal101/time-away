#!/usr/bin/env python3
"""
MCP Database Demo - Showcase Complex Query Capabilities
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from server.src.search.test_mcp_server import create_test_mcp_server
from server.src.db.connect import get_db
from server.src import logger


def demo_database_operations():
    """Demonstrate database operations through MCP server functions."""
    print("🎯 MCP Database Operations Demo")
    print("=" * 50)
    
    try:
        # Create MCP server
        server = create_test_mcp_server()
        print("✅ MCP Server created successfully")
        
        # Test 1: Database Connection Test
        print("\n🔍 1. Testing Database Connections...")
        if hasattr(server, 'test_read_connections_db'):
            result = server.test_read_connections_db()
            print(f"   📊 Database: {result.get('database_name')}")
            print(f"   📁 Collections: {result.get('collections')}")
            print(f"   ✅ Success: {result.get('success')}")
        
        # Test 2: Complex People Query
        print("\n🔍 2. Complex People Query...")
        if hasattr(server, 'complex_query_people'):
            result = server.complex_query_people(
                projection={"name": 1, "department": 1, "skills": 1, "_id": 0},
                limit=5
            )
            print(f"   📊 Found {result.get('count', 0)} people")
            print(f"   ✅ Success: {result.get('success')}")
            if result.get('results'):
                print("   👥 Sample people:")
                for person in result['results'][:2]:
                    print(f"     - {person.get('name')} ({person.get('department')})")
                    print(f"       Skills: {person.get('skills', [])}")
        
        # Test 3: Department Aggregation
        print("\n🔍 3. Department Aggregation...")
        if hasattr(server, 'aggregate_people_by_department'):
            result = server.aggregate_people_by_department()
            print(f"   📊 Total departments: {result.get('total_departments', 0)}")
            print(f"   ✅ Success: {result.get('success')}")
            if result.get('departments'):
                print("   🏢 Department breakdown:")
                for dept in result['departments'][:3]:
                    print(f"     - {dept.get('_id')}: {dept.get('count')} people")
        
        # Test 4: Skills Search
        print("\n🔍 4. Skills-Based Search...")
        if hasattr(server, 'search_people_by_skills'):
            result = server.search_people_by_skills(
                required_skills=["python", "javascript"],
                exact_match=False
            )
            print(f"   📊 Found {result.get('match_count', 0)} people with matching skills")
            print(f"   ✅ Success: {result.get('success')}")
            if result.get('matches'):
                print("   🛠️ People with matching skills:")
                for person in result['matches'][:2]:
                    print(f"     - {person.get('name')} ({person.get('department')})")
                    print(f"       Skills: {person.get('skills', [])}")
        
        # Test 5: Database Statistics
        print("\n🔍 5. Database Statistics...")
        if hasattr(server, 'get_database_stats'):
            result = server.get_database_stats()
            print(f"   📊 Total documents: {result.get('stats', {}).get('total_documents', 0)}")
            print(f"   ✅ Success: {result.get('success')}")
            if result.get('stats', {}).get('collections'):
                print("   📁 Collection breakdown:")
                for coll_name, coll_info in result['stats']['collections'].items():
                    print(f"     - {coll_name}: {coll_info.get('document_count', 0)} docs")
        
        print("\n🎉 All MCP operations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


def demo_complex_queries():
    """Demonstrate advanced query capabilities."""
    print("\n🔬 Advanced Query Demonstrations")
    print("=" * 50)
    
    try:
        server = create_test_mcp_server()
        
        # Advanced People Query with Filters
        print("\n🔍 Advanced People Query with Filters...")
        if hasattr(server, 'complex_query_people'):
            # Query 1: People in specific department with skills
            result1 = server.complex_query_people(
                filters={"department": "Human Resources"},
                projection={"name": 1, "skills": 1, "_id": 0},
                sort={"name": 1},
                limit=3
            )
            print(f"   📊 HR Department: {result1.get('count', 0)} people")
            
            # Query 2: People with specific skills
            result2 = server.complex_query_people(
                filters={"skills": {"$in": ["python", "javascript"]}},
                projection={"name": 1, "department": 1, "skills": 1, "_id": 0},
                limit=3
            )
            print(f"   📊 With Python/JS: {result2.get('count', 0)} people")
        
        # Advanced Task Query
        print("\n🔍 Advanced Task Query...")
        if hasattr(server, 'complex_query_tasks'):
            result = server.complex_query_tasks(
                projection={"task_id": 1, "name": 1, "_id": 0},
                sort={"name": 1},
                limit=3
            )
            print(f"   📊 Tasks found: {result.get('count', 0)}")
            if result.get('results'):
                print("   📋 Sample tasks:")
                for task in result['results'][:2]:
                    print(f"     - {task.get('task_id')}: {task.get('name')}")
        
        print("\n🎉 Advanced queries completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Advanced queries failed: {e}")
        return False


def main():
    """Run the complete MCP demo."""
    print("🚀 MCP Database Operations Demo")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run demos
    demos = [
        ("Basic Database Operations", demo_database_operations),
        ("Advanced Query Capabilities", demo_complex_queries)
    ]
    
    results = {}
    for demo_name, demo_func in demos:
        print(f"\n{'='*20} {demo_name} {'='*20}")
        try:
            success = demo_func()
            results[demo_name] = success
            print(f"{'✅ SUCCESS' if success else '❌ FAILED'}: {demo_name}")
        except Exception as e:
            results[demo_name] = False
            print(f"❌ FAILED: {demo_name} - {e}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 DEMO SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for demo_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {demo_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} demos successful ({passed/total*100:.1f}%)")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
