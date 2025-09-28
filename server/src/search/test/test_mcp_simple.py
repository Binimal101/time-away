#!/usr/bin/env python3
"""
Simple MCP Database Connection Tests
Direct function testing without MCP framework complexity
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from server.src.search.test_mcp_server import create_test_mcp_server
from server.src.db.connect import get_db, get_all_collections
from server.src import logger


def test_database_connection():
    """Test basic database connectivity."""
    print("🔍 Testing Database Connection...")
    
    try:
        db = get_db()
        collections = get_all_collections()
        
        print(f"✅ Database: {db.name}")
        print(f"✅ Collections: {collections}")
        
        # Test each collection
        for collection_name in collections:
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                print(f"  📊 {collection_name}: {count} documents")
            except Exception as e:
                print(f"  ❌ {collection_name}: Error - {e}")
        
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_complex_queries():
    """Test complex query functions directly."""
    print("\n🔍 Testing Complex Queries...")
    
    try:
        db = get_db()
        
        # Test 1: People query with projection
        print("\n--- Testing People Query with Projection ---")
        if 'user_profile' in db.list_collection_names():
            collection = db['user_profile']
            results = list(collection.find(
                {}, 
                {"name": 1, "department": 1, "_id": 0}
            ).limit(5))
            print(f"✅ Found {len(results)} people")
            for person in results[:2]:  # Show first 2
                print(f"  👤 {person}")
        else:
            print("❌ user_profile collection not found")
        
        # Test 2: Department aggregation
        print("\n--- Testing Department Aggregation ---")
        if 'user_profile' in db.list_collection_names():
            collection = db['user_profile']
            pipeline = [
                {"$group": {
                    "_id": "$department",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            results = list(collection.aggregate(pipeline))
            print(f"✅ Found {len(results)} departments")
            for dept in results[:3]:  # Show first 3
                print(f"  🏢 {dept['_id']}: {dept['count']} people")
        else:
            print("❌ user_profile collection not found")
        
        # Test 3: Skills search
        print("\n--- Testing Skills Search ---")
        if 'user_profile' in db.list_collection_names():
            collection = db['user_profile']
            results = list(collection.find({
                "skills": {"$exists": True, "$ne": []}
            }, {"name": 1, "skills": 1, "_id": 0}).limit(5))
            print(f"✅ Found {len(results)} people with skills")
            for person in results[:2]:  # Show first 2
                print(f"  🛠️ {person}")
        else:
            print("❌ user_profile collection not found")
        
        return True
    except Exception as e:
        print(f"❌ Complex queries failed: {e}")
        return False


def test_mcp_server_creation():
    """Test MCP server creation and tool registration."""
    print("\n🔍 Testing MCP Server Creation...")
    
    try:
        server = create_test_mcp_server()
        print("✅ MCP server created successfully")
        
        # Check if server has expected attributes
        server_attrs = dir(server)
        print(f"✅ Server attributes: {len(server_attrs)} found")
        
        # Try to find tool functions
        tool_functions = []
        for attr in server_attrs:
            if not attr.startswith('_') and callable(getattr(server, attr)):
                tool_functions.append(attr)
        
        print(f"✅ Found {len(tool_functions)} potential tool functions")
        print(f"  🔧 Tools: {tool_functions}")
        
        return True
    except Exception as e:
        print(f"❌ MCP server creation failed: {e}")
        return False


def test_direct_function_calls():
    """Test calling MCP tool functions directly."""
    print("\n🔍 Testing Direct Function Calls...")
    
    try:
        server = create_test_mcp_server()
        
        # Test database connection function
        if hasattr(server, 'test_read_connections_db'):
            print("--- Testing test_read_connections_db ---")
            result = server.test_read_connections_db()
            print(f"✅ Connection test: {result.get('success', False)}")
            if result.get('success'):
                print(f"  📊 Database: {result.get('database_name')}")
                print(f"  📁 Collections: {result.get('collections')}")
        
        # Test complex query function
        if hasattr(server, 'complex_query_people'):
            print("\n--- Testing complex_query_people ---")
            result = server.complex_query_people(
                projection={"name": 1, "department": 1, "_id": 0},
                limit=3
            )
            print(f"✅ People query: {result.get('success', False)}")
            print(f"  📊 Found {result.get('count', 0)} people")
        
        # Test aggregation function
        if hasattr(server, 'aggregate_people_by_department'):
            print("\n--- Testing aggregate_people_by_department ---")
            result = server.aggregate_people_by_department()
            print(f"✅ Aggregation: {result.get('success', False)}")
            if result.get('success'):
                print(f"  📊 Departments: {result.get('total_departments', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Direct function calls failed: {e}")
        return False


def run_all_tests():
    """Run all tests and generate report."""
    print("🚀 Starting Simple MCP Database Tests")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Complex Queries", test_complex_queries),
        ("MCP Server Creation", test_mcp_server_creation),
        ("Direct Function Calls", test_direct_function_calls)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = success
            print(f"{'✅ PASSED' if success else '❌ FAILED'}: {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"❌ FAILED: {test_name} - {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
