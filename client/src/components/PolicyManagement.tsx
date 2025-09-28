import React, { useState } from 'react';
import { Shield, Plus, CreditCard as Edit, Trash2, Save, X, Calendar, Clock, AlertTriangle } from 'lucide-react';

interface PTOPolicy {
  id: string;
  name: string;
  department: string;
  vacationDays: number;
  sickDays: number;
  personalDays: number;
  carryOverLimit: number;
  maxConsecutiveDays: number;
  advanceNoticeRequired: number;
  blackoutPeriods: string[];
}

export const PolicyManagement: React.FC = () => {
  const [policies, setPolicies] = useState<PTOPolicy[]>([
    {
      id: '1',
      name: 'Standard Employee Policy',
      department: 'All Departments',
      vacationDays: 20,
      sickDays: 10,
      personalDays: 5,
      carryOverLimit: 5,
      maxConsecutiveDays: 10,
      advanceNoticeRequired: 14,
      blackoutPeriods: ['2025-12-20 to 2025-12-31', '2025-07-01 to 2025-07-07']
    },
    {
      id: '2',
      name: 'Senior Employee Policy',
      department: 'All Departments',
      vacationDays: 25,
      sickDays: 12,
      personalDays: 7,
      carryOverLimit: 10,
      maxConsecutiveDays: 15,
      advanceNoticeRequired: 21,
      blackoutPeriods: ['2025-12-20 to 2025-12-31']
    },
    {
      id: '3',
      name: 'Engineering Policy',
      department: 'Engineering',
      vacationDays: 22,
      sickDays: 10,
      personalDays: 6,
      carryOverLimit: 7,
      maxConsecutiveDays: 12,
      advanceNoticeRequired: 14,
      blackoutPeriods: ['2025-12-20 to 2025-12-31', '2025-03-15 to 2025-03-22']
    }
  ]);

  const [editingPolicy, setEditingPolicy] = useState<PTOPolicy | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<Partial<PTOPolicy>>({});

  const handleEdit = (policy: PTOPolicy) => {
    setEditingPolicy(policy);
    setFormData(policy);
    setShowForm(true);
  };

  const handleCreate = () => {
    setEditingPolicy(null);
    setFormData({
      name: '',
      department: '',
      vacationDays: 20,
      sickDays: 10,
      personalDays: 5,
      carryOverLimit: 5,
      maxConsecutiveDays: 10,
      advanceNoticeRequired: 14,
      blackoutPeriods: []
    });
    setShowForm(true);
  };

  const handleSave = () => {
    if (editingPolicy) {
      setPolicies(prev => prev.map(p => p.id === editingPolicy.id ? { ...formData as PTOPolicy } : p));
    } else {
      const newPolicy: PTOPolicy = {
        ...formData as PTOPolicy,
        id: Date.now().toString()
      };
      setPolicies(prev => [...prev, newPolicy]);
    }
    setShowForm(false);
    setEditingPolicy(null);
    setFormData({});
  };

  const handleDelete = (policyId: string) => {
    if (confirm('Are you sure you want to delete this policy?')) {
      setPolicies(prev => prev.filter(p => p.id !== policyId));
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingPolicy(null);
    setFormData({});
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">PTO Policy Management</h2>
          <p className="text-gray-600">Configure and manage time off policies for different departments and roles</p>
        </div>
        <button
          onClick={handleCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Create Policy</span>
        </button>
      </div>

      {/* Policy Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {policies.map((policy) => (
          <div key={policy.id} className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">{policy.name}</h3>
              </div>
              <div className="flex space-x-1">
                <button
                  onClick={() => handleEdit(policy)}
                  className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                >
                  <Edit className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDelete(policy.id)}
                  className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Department:</span>
                <span className="font-medium text-gray-900">{policy.department}</span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="text-center p-2 bg-blue-50 rounded">
                  <div className="font-medium text-blue-700">{policy.vacationDays}</div>
                  <div className="text-xs text-blue-600">Vacation</div>
                </div>
                <div className="text-center p-2 bg-red-50 rounded">
                  <div className="font-medium text-red-700">{policy.sickDays}</div>
                  <div className="text-xs text-red-600">Sick</div>
                </div>
                <div className="text-center p-2 bg-green-50 rounded">
                  <div className="font-medium text-green-700">{policy.personalDays}</div>
                  <div className="text-xs text-green-600">Personal</div>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Carry Over Limit:</span>
                  <span className="font-medium">{policy.carryOverLimit} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Max Consecutive:</span>
                  <span className="font-medium">{policy.maxConsecutiveDays} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Advance Notice:</span>
                  <span className="font-medium">{policy.advanceNoticeRequired} days</span>
                </div>
              </div>

              {policy.blackoutPeriods.length > 0 && (
                <div className="mt-3 p-2 bg-yellow-50 rounded">
                  <div className="flex items-center space-x-1 mb-1">
                    <AlertTriangle className="h-3 w-3 text-yellow-600" />
                    <span className="text-xs font-medium text-yellow-700">Blackout Periods</span>
                  </div>
                  <div className="text-xs text-yellow-600">
                    {policy.blackoutPeriods.slice(0, 2).map((period, index) => (
                      <div key={index}>{period}</div>
                    ))}
                    {policy.blackoutPeriods.length > 2 && (
                      <div>+{policy.blackoutPeriods.length - 2} more</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Policy Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {editingPolicy ? 'Edit Policy' : 'Create New Policy'}
                </h3>
                <button
                  onClick={handleCancel}
                  className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Policy Name
                  </label>
                  <input
                    type="text"
                    value={formData.name || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Standard Employee Policy"
                  />
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
                    <option value="All Departments">All Departments</option>
                    <option value="Engineering">Engineering</option>
                    <option value="Marketing">Marketing</option>
                    <option value="Sales">Sales</option>
                    <option value="HR">HR</option>
                  </select>
                </div>
              </div>

              {/* PTO Allocations */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">PTO Allocations (Annual)</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Vacation Days
                    </label>
                    <input
                      type="number"
                      value={formData.vacationDays || 0}
                      onChange={(e) => setFormData(prev => ({ ...prev, vacationDays: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Sick Days
                    </label>
                    <input
                      type="number"
                      value={formData.sickDays || 0}
                      onChange={(e) => setFormData(prev => ({ ...prev, sickDays: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Personal Days
                    </label>
                    <input
                      type="number"
                      value={formData.personalDays || 0}
                      onChange={(e) => setFormData(prev => ({ ...prev, personalDays: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Policy Rules */}
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Policy Rules</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Carry Over Limit (days)
                    </label>
                    <input
                      type="number"
                      value={formData.carryOverLimit || 0}
                      onChange={(e) => setFormData(prev => ({ ...prev, carryOverLimit: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Consecutive Days
                    </label>
                    <input
                      type="number"
                      value={formData.maxConsecutiveDays || 0}
                      onChange={(e) => setFormData(prev => ({ ...prev, maxConsecutiveDays: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Advance Notice (days)
                    </label>
                    <input
                      type="number"
                      value={formData.advanceNoticeRequired || 0}
                      onChange={(e) => setFormData(prev => ({ ...prev, advanceNoticeRequired: parseInt(e.target.value) }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Blackout Periods */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Blackout Periods
                </label>
                <textarea
                  value={formData.blackoutPeriods?.join('\n') || ''}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    blackoutPeriods: e.target.value.split('\n').filter(p => p.trim()) 
                  }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter blackout periods, one per line (e.g., 2025-12-20 to 2025-12-31)"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Enter date ranges when PTO requests are not allowed, one per line
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
                <span>{editingPolicy ? 'Update Policy' : 'Create Policy'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};