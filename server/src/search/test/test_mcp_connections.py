#!/usr/bin/env python3
"""
Comprehensive tests for MCP database connections and complex queries
"""

import os
import sys
import json
import unittest
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from server.src.search.test_mcp_server import create_test_mcp_server
from server.src.db.connect import get_db
from server.src import logger


class TestMCPConnections(unittest.TestCase):
    """Test suite for MCP database connections and complex queries."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.mcp_server = create_test_mcp_server()
        cls.db = get_db()
        logger.info("Test environment initialized")
    
    def test_read_connections_db(self):
        """Test basic database connection functionality."""
        print("\n=== Testing Database Connections ===")
        
        # Get the test_read_connections_db tool function directly
        tool_func = getattr(self.mcp_server, 'test_read_connections_db', None)
        if not tool_func:
            # Try to find it in the server's registered tools
            for attr_name in dir(self.mcp_server):
                if attr_name == "test_read_connections_db":
                    tool_func = getattr(self.mcp_server, attr_name)
                    break
        
        self.assertIsNotNone(tool_func, "test_read_connections_db tool not found")
        
        # Execute the tool
        result = tool_func()
        
        print(f"Connection test result: {json.dumps(result, indent=2, default=str)}")
        
        # Assertions
        self.assertTrue(result.get("success", False), f"Connection failed: {result.get('error')}")
        self.assertIn("database_name", result)
        self.assertIn("collections", result)
        self.assertIn("collection_stats", result)
        
        print(f"✅ Database: {result['database_name']}")
        print(f"✅ Collections: {result['collections']}")
        
        return result
    
    def test_complex_query_people(self):
        """Test complex people queries with various filters."""
        print("\n=== Testing Complex People Queries ===")
        
        # Get the complex_query_people tool
        tool = None
        for t in self.mcp_server.tools:
            if t.name == "complex_query_people":
                tool = t
                break
        
        self.assertIsNotNone(tool, "complex_query_people tool not found")
        
        # Test 1: Basic query with projection
        print("\n--- Test 1: Basic query with projection ---")
        result1 = tool.func(
            projection={"name": 1, "department": 1, "_id": 0},
            limit=5
        )
        print(f"Basic query result: {json.dumps(result1, indent=2, default=str)}")
        self.assertTrue(result1.get("success", False))
        
        # Test 2: Department filter
        print("\n--- Test 2: Department filter ---")
        result2 = tool.func(
            filters={"department": {"$exists": True}},
            projection={"name": 1, "department": 1, "skills": 1, "_id": 0},
            limit=10
        )
        print(f"Department filter result: {json.dumps(result2, indent=2, default=str)}")
        self.assertTrue(result2.get("success", False))
        
        # Test 3: Skills filter
        print("\n--- Test 3: Skills filter ---")
        result3 = tool.func(
            filters={"skills": {"$exists": True, "$ne": []}},
            projection={"name": 1, "skills": 1, "_id": 0},
            limit=10
        )
        print(f"Skills filter result: {json.dumps(result3, indent=2, default=str)}")
        self.assertTrue(result3.get("success", False))
        
        return [result1, result2, result3]
    
    def test_complex_query_tasks(self):
        """Test complex task queries."""
        print("\n=== Testing Complex Task Queries ===")
        
        # Get the complex_query_tasks tool
        tool = None
        for t in self.mcp_server.tools:
            if t.name == "complex_query_tasks":
                tool = t
                break
        
        self.assertIsNotNone(tool, "complex_query_tasks tool not found")
        
        # Test 1: Basic task query
        print("\n--- Test 1: Basic task query ---")
        result1 = tool.func(
            projection={"task_id": 1, "name": 1, "_id": 0},
            limit=5
        )
        print(f"Basic task query: {json.dumps(result1, indent=2, default=str)}")
        self.assertTrue(result1.get("success", False))
        
        # Test 2: Date range filter (if tasks have date fields)
        print("\n--- Test 2: Date range filter ---")
        result2 = tool.func(
            filters={"start_epoch": {"$exists": True}},
            projection={"task_id": 1, "name": 1, "start_epoch": 1, "_id": 0},
            limit=10
        )
        print(f"Date range filter: {json.dumps(result2, indent=2, default=str)}")
        self.assertTrue(result2.get("success", False))
        
        return [result1, result2]
    
    def test_aggregate_people_by_department(self):
        """Test aggregation of people by department."""
        print("\n=== Testing People Aggregation by Department ===")
        
        # Get the aggregate_people_by_department tool
        tool = None
        for t in self.mcp_server.tools:
            if t.name == "aggregate_people_by_department":
                tool = t
                break
        
        self.assertIsNotNone(tool, "aggregate_people_by_department tool not found")
        
        result = tool.func()
        print(f"Aggregation result: {json.dumps(result, indent=2, default=str)}")
        
        self.assertTrue(result.get("success", False))
        self.assertIn("departments", result)
        self.assertIn("total_departments", result)
        
        print(f"✅ Total departments: {result['total_departments']}")
        
        return result
    
    def test_search_people_by_skills(self):
        """Test skill-based people search."""
        print("\n=== Testing Skill-Based People Search ===")
        
        # Get the search_people_by_skills tool
        tool = None
        for t in self.mcp_server.tools:
            if t.name == "search_people_by_skills":
                tool = t
                break
        
        self.assertIsNotNone(tool, "search_people_by_skills tool not found")
        
        # Test 1: Any skill match
        print("\n--- Test 1: Any skill match ---")
        result1 = tool.func(
            required_skills=["python", "javascript", "java"],
            exact_match=False
        )
        print(f"Any skill match: {json.dumps(result1, indent=2, default=str)}")
        self.assertTrue(result1.get("success", False))
        
        # Test 2: Exact skill match
        print("\n--- Test 2: Exact skill match ---")
        result2 = tool.func(
            required_skills=["python"],
            exact_match=True
        )
        print(f"Exact skill match: {json.dumps(result2, indent=2, default=str)}")
        self.assertTrue(result2.get("success", False))
        
        # Test 3: Department + skill filter
        print("\n--- Test 3: Department + skill filter ---")
        result3 = tool.func(
            required_skills=["python", "javascript"],
            department="Engineering",
            exact_match=False
        )
        print(f"Department + skill filter: {json.dumps(result3, indent=2, default=str)}")
        self.assertTrue(result3.get("success", False))
        
        return [result1, result2, result3]
    
    def test_get_database_stats(self):
        """Test comprehensive database statistics."""
        print("\n=== Testing Database Statistics ===")
        
        # Get the get_database_stats tool
        tool = None
        for t in self.mcp_server.tools:
            if t.name == "get_database_stats":
                tool = t
                break
        
        self.assertIsNotNone(tool, "get_database_stats tool not found")
        
        result = tool.func()
        print(f"Database stats: {json.dumps(result, indent=2, default=str)}")
        
        self.assertTrue(result.get("success", False))
        self.assertIn("stats", result)
        self.assertIn("database_name", result["stats"])
        self.assertIn("collections", result["stats"])
        
        print(f"✅ Database: {result['stats']['database_name']}")
        print(f"✅ Total documents: {result['stats']['total_documents']}")
        
        return result
    
    def test_all_tools_available(self):
        """Test that all expected tools are available."""
        print("\n=== Testing Tool Availability ===")
        
        expected_tools = [
            "test_read_connections_db",
            "complex_query_people", 
            "complex_query_tasks",
            "aggregate_people_by_department",
            "search_people_by_skills",
            "get_database_stats"
        ]
        
        available_tools = [tool.name for tool in self.mcp_server.tools]
        print(f"Available tools: {available_tools}")
        
        for tool_name in expected_tools:
            self.assertIn(tool_name, available_tools, f"Tool {tool_name} not found")
            print(f"✅ {tool_name}")
        
        return available_tools


def run_comprehensive_test():
    """Run all tests and generate a comprehensive report."""
    print("🚀 Starting Comprehensive MCP Database Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMCPConnections)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate report
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
