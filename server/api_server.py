#!/usr/bin/env python3
"""
Simple API server for Time Away application
Provides REST endpoints for frontend to connect to database
"""

import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database functions
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db.connect import get_db, get_user_profile_collection, get_dept_collection

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

@app.route('/api/departments', methods=['GET'])
def get_departments():
    """Get all departments with employee counts"""
    try:
        db = get_db()
        user_profile_collection = get_user_profile_collection()
        
        # Get all departments with employee counts
        pipeline = [
            {
                "$group": {
                    "_id": "$department",
                    "employee_count": {"$sum": 1},
                    "roles": {"$addToSet": "$role"}
                }
            },
            {
                "$project": {
                    "department": "$_id",
                    "employee_count": 1,
                    "roles": 1,
                    "_id": 0
                }
            },
            {
                "$sort": {"employee_count": -1}
            }
        ]
        
        departments = list(user_profile_collection.aggregate(pipeline))
        
        return jsonify({
            "success": True,
            "departments": departments,
            "total_departments": len(departments)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "departments": []
        }), 500

@app.route('/api/departments/<department_name>/employees', methods=['GET'])
def get_department_employees(department_name):
    """Get all employees in a specific department"""
    try:
        user_profile_collection = get_user_profile_collection()
        
        employees = list(user_profile_collection.find(
            {"department": department_name},
            {"_id": 1, "name": 1, "email": 1, "role": 1, "jobTitle": 1, "skills": 1, "level": 1}
        ))
        
        # Convert ObjectId to string for JSON serialization
        for employee in employees:
            if '_id' in employee:
                employee['_id'] = str(employee['_id'])
        
        return jsonify({
            "success": True,
            "employees": employees,
            "department": department_name,
            "count": len(employees)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "employees": []
        }), 500

@app.route('/api/employees', methods=['GET'])
def get_all_employees():
    """Get all employees with their details"""
    try:
        user_profile_collection = get_user_profile_collection()
        
        employees = list(user_profile_collection.find(
            {},
            {"_id": 1, "name": 1, "email": 1, "role": 1, "department": 1, "jobTitle": 1, "skills": 1, "level": 1}
        ))
        
        # Convert ObjectId to string for JSON serialization
        for employee in employees:
            if '_id' in employee:
                employee['_id'] = str(employee['_id'])
        
        return jsonify({
            "success": True,
            "employees": employees,
            "count": len(employees)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "employees": []
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db = get_db()
        # Test database connection
        db.command('ping')
        return jsonify({
            "success": True,
            "status": "healthy",
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting API server on port {port}")
    print(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
