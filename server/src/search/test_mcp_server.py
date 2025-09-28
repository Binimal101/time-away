#!/usr/bin/env python3
"""
Separate MCP Test Server for Database Operations
Provides read-only access with complex query capabilities
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from server.src.db.connect import get_db, get_all_collections
from server.src import logger


def create_test_mcp_server() -> FastMCP:
    """Create a test MCP server with complex query capabilities."""
    load_dotenv()
    mcp = FastMCP("test-database-mcp")

    @mcp.tool()
    def test_read_connections_db() -> Dict[str, Any]:
        """Test database connections and return available collections.
        
        Returns:
            Dictionary with connection status and available collections
        """
        try:
            db = get_db()
            collections = get_all_collections()
            
            # Test each collection for basic connectivity
            collection_stats = {}
            for collection_name in collections:
                try:
                    collection = db[collection_name]
                    count = collection.count_documents({})
                    collection_stats[collection_name] = {
                        "document_count": count,
                        "accessible": True
                    }
                except Exception as e:
                    collection_stats[collection_name] = {
                        "document_count": 0,
                        "accessible": False,
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "database_name": db.name,
                "collections": collections,
                "collection_stats": collection_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error testing database connections: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @mcp.tool()
    def complex_query_people(filters: Optional[Dict[str, Any]] = None, 
                            projection: Optional[Dict[str, int]] = None,
                            limit: int = 100,
                            sort: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Complex query on people/user profiles with advanced filtering.
        
        Args:
            filters: MongoDB query filters (e.g., {"department": "Engineering", "skills": {"$in": ["python"]}})
            projection: Fields to include/exclude (e.g., {"name": 1, "_id": 0})
            limit: Maximum number of results
            sort: Sort criteria (e.g., {"name": 1, "department": -1})
            
        Returns:
            Dictionary with query results and metadata
        """
        try:
            db = get_db()
            if 'user_profile' not in db.list_collection_names():
                return {
                    "success": False,
                    "error": "user_profile collection not found",
                    "results": [],
                    "count": 0
                }
            
            collection = db['user_profile']
            
            # Build query
            query = filters or {}
            
            # Execute query with options
            cursor = collection.find(query, projection)
            
            if sort:
                cursor = cursor.sort(list(sort.items()))
            
            if limit > 0:
                cursor = cursor.limit(limit)
            
            results = list(cursor)
            
            return {
                "success": True,
                "query": query,
                "projection": projection,
                "sort": sort,
                "limit": limit,
                "results": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in complex people query: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "count": 0
            }

    @mcp.tool()
    def complex_query_tasks(filters: Optional[Dict[str, Any]] = None,
                          projection: Optional[Dict[str, int]] = None,
                          limit: int = 100,
                          sort: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """Complex query on tasks with advanced filtering.
        
        Args:
            filters: MongoDB query filters
            projection: Fields to include/exclude
            limit: Maximum number of results
            sort: Sort criteria
            
        Returns:
            Dictionary with query results and metadata
        """
        try:
            db = get_db()
            if 'tasks' not in db.list_collection_names():
                return {
                    "success": False,
                    "error": "tasks collection not found",
                    "results": [],
                    "count": 0
                }
            
            collection = db['tasks']
            
            # Build query
            query = filters or {}
            
            # Execute query with options
            cursor = collection.find(query, projection)
            
            if sort:
                cursor = cursor.sort(list(sort.items()))
            
            if limit > 0:
                cursor = cursor.limit(limit)
            
            results = list(cursor)
            
            return {
                "success": True,
                "query": query,
                "projection": projection,
                "sort": sort,
                "limit": limit,
                "results": results,
                "count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in complex tasks query: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "count": 0
            }

    @mcp.tool()
    def aggregate_people_by_department() -> Dict[str, Any]:
        """Aggregate people by department with statistics.
        
        Returns:
            Dictionary with department statistics
        """
        try:
            db = get_db()
            if 'user_profile' not in db.list_collection_names():
                return {
                    "success": False,
                    "error": "user_profile collection not found",
                    "departments": []
                }
            
            collection = db['user_profile']
            
            # Aggregation pipeline
            pipeline = [
                {"$group": {
                    "_id": "$department",
                    "count": {"$sum": 1},
                    "people": {"$push": {
                        "person_id": "$person_id",
                        "name": "$name",
                        "skills": "$skills"
                    }}
                }},
                {"$sort": {"count": -1}}
            ]
            
            results = list(collection.aggregate(pipeline))
            
            return {
                "success": True,
                "departments": results,
                "total_departments": len(results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error aggregating people by department: {e}")
            return {
                "success": False,
                "error": str(e),
                "departments": []
            }

    @mcp.tool()
    def search_people_by_skills(required_skills: List[str],
                               department: Optional[str] = None,
                               exact_match: bool = False) -> Dict[str, Any]:
        """Search people by skills with optional department filter.
        
        Args:
            required_skills: List of skills to search for
            department: Optional department filter
            exact_match: If True, person must have ALL skills; if False, person must have ANY skill
            
        Returns:
            Dictionary with matching people
        """
        try:
            db = get_db()
            if 'user_profile' not in db.list_collection_names():
                return {
                    "success": False,
                    "error": "user_profile collection not found",
                    "matches": []
                }
            
            collection = db['user_profile']
            
            # Build query based on exact_match
            if exact_match:
                # Person must have ALL required skills
                skills_query = {"$all": required_skills}
            else:
                # Person must have ANY of the required skills
                skills_query = {"$in": required_skills}
            
            query = {"skills": skills_query}
            
            if department:
                query["department"] = department
            
            results = list(collection.find(query))
            
            return {
                "success": True,
                "required_skills": required_skills,
                "department_filter": department,
                "exact_match": exact_match,
                "matches": results,
                "match_count": len(results),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error searching people by skills: {e}")
            return {
                "success": False,
                "error": str(e),
                "matches": []
            }

    @mcp.tool()
    def get_database_stats() -> Dict[str, Any]:
        """Get comprehensive database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            db = get_db()
            collections = get_all_collections()
            
            stats = {
                "database_name": db.name,
                "collections": {},
                "total_documents": 0
            }
            
            for collection_name in collections:
                try:
                    collection = db[collection_name]
                    count = collection.count_documents({})
                    stats["collections"][collection_name] = {
                        "document_count": count,
                        "accessible": True
                    }
                    stats["total_documents"] += count
                except Exception as e:
                    stats["collections"][collection_name] = {
                        "document_count": 0,
                        "accessible": False,
                        "error": str(e)
                    }
            
            return {
                "success": True,
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    return mcp


def run_test_mcp_server() -> None:
    """Run the test MCP server."""
    server = create_test_mcp_server()
    logger.info("Starting Test MCP Server...")
    server.run()


if __name__ == "__main__":
    run_test_mcp_server()
