import React, { useState } from 'react';
import { Users, Plus, CreditCard as Edit, Trash2, Save, X, Search, Filter, Mail, Phone, MapPin, Award, Briefcase } from 'lucide-react';
import { Employee, PTOBalance } from '../types';

interface TeamManagementProps {
  employees: Employee[];
  balances: PTOBalance[];
  onUpdateEmployee: (employee: Employee) => void;
  onAddEmployee: (employee: Omit<Employee, 'id'>) => void;
  onDeleteEmployee: (employeeId: string) => void;
}

export const TeamManagement: React.FC<TeamManagementProps> = ({
  employees,
  balances,
  onUpdateEmployee,
  onAddEmployee,
  onDeleteEmployee
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [formData, setFormData] = useState<Partial<Employee>>({});

  const departments = [...new Set(employees.map(emp => emp.department))];

  const filteredEmployees = employees.filter(employee => {
    const matchesSearch = employee.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         employee.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         employee.jobTitle?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDepartment = departmentFilter === 'all' || employee.department === departmentFilter;
    return matchesSearch && matchesDepartment;
  });

  const handleEdit = (employee: Employee) => {
    setEditingEmployee(employee);
    setFormData(employee);
    setShowForm(true);
  };

  const handleCreate = () => {
    setEditingEmployee(null);
    setFormData({
      name: '',
      email: '',
      role: 'employee',
      department: '',
      jobTitle: '',
      skills: [],
      level: 'junior'
    });
    setShowForm(true);
  };

  const handleSave = () => {
    if (editingEmployee) {
      onUpdateEmployee({ ...editingEmployee, ...formData } as Employee);
    } else {
      onAddEmployee(formData as Omit<Employee, 'id'>);
    }
    setShowForm(false);
    setEditingEmployee(null);
    setFormData({});
  };

  const handleDelete = (employeeId: string) => {
    if (confirm('Are you sure you want to delete this employee?')) {
      onDeleteEmployee(employeeId);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingEmployee(null);
    setFormData({});
  };

  const getLevelBadgeColor = (level: string) => {
    switch (level) {
      case 'junior': return 'bg-blue-100 text-blue-700';
      case 'mid': return 'bg-green-100 text-green-700';
      case 'senior': return 'bg-purple-100 text-purple-700';
      case 'lead': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Team Management</h2>
          <p className="text-gray-600">Manage your team members and their information</p>
        </div>
        <button
          onClick={handleCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Add Employee</span>
        </button>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search employees..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Departments</option>
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Employee Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredEmployees.map((employee) => {
          const balance = balances.find(b => b.employeeId === employee.id);
          return (
            <div key={employee.id} className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{employee.name}</h3>
                  <p className="text-sm text-gray-600">{employee.jobTitle || 'No title'}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getLevelBadgeColor(employee.level || 'junior')}`}>
                      {(employee.level || 'junior').charAt(0).toUpperCase() + (employee.level || 'junior').slice(1)}
                    </span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      employee.role === 'manager' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {employee.role.charAt(0).toUpperCase() + employee.role.slice(1)}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-1">
                  <button
                    onClick={() => handleEdit(employee)}
                    className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(employee.id)}
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex items-center text-gray-600">
                  <Mail className="h-3 w-3 mr-2" />
                  {employee.email}
                </div>
                <div className="flex items-center text-gray-600">
                  <Briefcase className="h-3 w-3 mr-2" />
                  {employee.department}
                </div>
              </div>

              {employee.skills && Array.isArray(employee.skills) && employee.skills.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-gray-700 mb-1">Skills</p>
                  <div className="flex flex-wrap gap-1">
                    {employee.skills.slice(0, 3).map((skill, index) => (
                      <span key={index} className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">
                        {skill}
                      </span>
                    ))}
                    {employee.skills.length > 3 && (
                      <span className="px-2 py-1 text-xs bg-gray-50 text-gray-600 rounded">
                        +{employee.skills.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              {balance && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs font-medium text-gray-700 mb-1">PTO Balance</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="text-center">
                      <div className="font-medium text-blue-600">{balance.vacation}</div>
                      <div className="text-gray-500">Vacation</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium text-red-600">{balance.sick}</div>
                      <div className="text-gray-500">Sick</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium text-green-600">{balance.personal}</div>
                      <div className="text-gray-500">Personal</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Employee Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {editingEmployee ? 'Edit Employee' : 'Add New Employee'}
                </h3>
                <button
                  onClick={handleCancel}
                  className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter full name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  value={formData.email || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter email address"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Title
                </label>
                <input
                  type="text"
                  value={formData.jobTitle || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, jobTitle: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter job title"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role
                  </label>
                  <select
                    value={formData.role || 'employee'}
                    onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value as 'employee' | 'manager' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="employee">Employee</option>
                    <option value="manager">Manager</option>
                  </select>
                </div>
              
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Level
                  </label>
                  <select
                    value={formData.level || 'junior'}
                    onChange={(e) => setFormData(prev => ({ ...prev, level: e.target.value as 'junior' | 'mid' | 'senior' | 'lead' }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="junior">Junior</option>
                    <option value="mid">Mid-Level</option>
                    <option value="senior">Senior</option>
                    <option value="lead">Lead</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Department
                </label>
                <select
                  value={formData.department || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, department: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select Department</option>
                  <option value="Engineering">Engineering</option>
                  <option value="Marketing">Marketing</option>
                  <option value="Sales">Sales</option>
                  <option value="HR">HR</option>
                  <option value="Finance">Finance</option>
                </select>
              </div>

              {formData.role === 'employee' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Manager
                  </label>
                  <select
                    value={formData.managerId || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, managerId: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Manager</option>
                    {employees.filter(emp => emp.role === 'manager').map(manager => (
                      <option key={manager.id} value={manager.id}>{manager.name}</option>
                    ))}
                  </select>
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Skills (comma-separated)
                </label>
                <textarea
                  value={formData.skills?.join(', ') || ''}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    skills: e.target.value.split(',').map(s => s.trim()).filter(s => s) 
                  }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="React, Node.js, Python, AWS, etc."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Enter skills separated by commas
                </p>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={handleCancel}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <Save className="h-4 w-4" />
                <span>{editingEmployee ? 'Update Employee' : 'Add Employee'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};