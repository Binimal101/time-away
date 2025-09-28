import React from 'react';
import { TrendingUp, Users, Calendar, Clock, BarChart3, PieChart, Activity } from 'lucide-react';
import { PTORequest, Employee, PTOBalance } from '../types';

interface AnalyticsProps {
  requests: PTORequest[];
  employees: Employee[];
  balances: PTOBalance[];
}

export const Analytics: React.FC<AnalyticsProps> = ({ requests, employees, balances }) => {
  // Calculate analytics data
  const totalEmployees = employees.length;
  const totalPTODays = balances.reduce((sum, b) => sum + b.totalAvailable + b.totalUsed, 0);
  const usedPTODays = balances.reduce((sum, b) => sum + b.totalUsed, 0);
  const pendingRequests = requests.filter(r => r.status === 'pending').length;
  const approvedRequests = requests.filter(r => r.status === 'approved').length;
  const approvalRate = requests.length > 0 ? Math.round((approvedRequests / requests.length) * 100) : 0;
  const averageRequestDays = requests.length > 0 ? Math.round(requests.reduce((sum, r) => sum + r.days, 0) / requests.length) : 0;

  // Department breakdown
  const departmentStats = employees.reduce((acc, emp) => {
    const dept = emp.department;
    if (!acc[dept]) {
      acc[dept] = { employees: 0, ptoUsed: 0, totalPTO: 0 };
    }
    acc[dept].employees++;
    
    const balance = balances.find(b => b.employeeId === emp.id);
    if (balance) {
      acc[dept].ptoUsed += balance.totalUsed;
      acc[dept].totalPTO += balance.totalAvailable + balance.totalUsed;
    }
    return acc;
  }, {} as Record<string, { employees: number; ptoUsed: number; totalPTO: number }>);

  // Monthly trends (mock data for demo)
  const monthlyTrends = [
    { month: 'Jan', requests: 12, daysUsed: 45 },
    { month: 'Feb', requests: 8, daysUsed: 32 },
    { month: 'Mar', requests: 15, daysUsed: 58 },
    { month: 'Apr', requests: 18, daysUsed: 67 },
    { month: 'May', requests: 22, daysUsed: 89 },
    { month: 'Jun', requests: 25, daysUsed: 95 }
  ];

  const kpiCards = [
    {
      title: 'Total Employees',
      value: totalEmployees,
      change: '+2 this month',
      changeType: 'positive',
      icon: Users,
      color: 'blue'
    },
    {
      title: 'PTO Utilization',
      value: `${Math.round((usedPTODays / totalPTODays) * 100)}%`,
      change: '+5% from last month',
      changeType: 'positive',
      icon: TrendingUp,
      color: 'green'
    },
    {
      title: 'Approval Rate',
      value: `${approvalRate}%`,
      change: 'Consistent',
      changeType: 'neutral',
      icon: BarChart3,
      color: 'purple'
    },
    {
      title: 'Avg Request Days',
      value: averageRequestDays,
      change: '-0.5 days',
      changeType: 'positive',
      icon: Clock,
      color: 'orange'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
        <p className="text-gray-600">Comprehensive insights into team PTO usage and trends</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div key={kpi.title} className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">{kpi.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{kpi.value}</p>
                  <p className={`text-xs mt-1 ${
                    kpi.changeType === 'positive' ? 'text-green-600' :
                    kpi.changeType === 'negative' ? 'text-red-600' : 'text-gray-500'
                  }`}>
                    {kpi.change}
                  </p>
                </div>
                <div className={`p-3 rounded-lg bg-${kpi.color}-50`}>
                  <Icon className={`h-6 w-6 text-${kpi.color}-600`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trends */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center mb-6">
            <Activity className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Monthly Trends</h3>
          </div>
          <div className="space-y-4">
            {monthlyTrends.map((month, index) => (
              <div key={month.month} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-8 text-sm font-medium text-gray-600">{month.month}</div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${(month.requests / 30) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600">{month.requests} requests</span>
                    </div>
                  </div>
                </div>
                <div className="text-sm font-medium text-gray-900">{month.daysUsed} days</div>
              </div>
            ))}
          </div>
        </div>

        {/* Department Breakdown */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <div className="flex items-center mb-6">
            <PieChart className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Department Breakdown</h3>
          </div>
          <div className="space-y-4">
            {Object.entries(departmentStats).map(([dept, stats]) => {
              const utilizationRate = stats.totalPTO > 0 ? Math.round((stats.ptoUsed / stats.totalPTO) * 100) : 0;
              return (
                <div key={dept} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-900">{dept}</span>
                    <span className="text-sm text-gray-600">{stats.employees} employees</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${utilizationRate}%` }}
                      ></div>
                    </div>
                    <span className="text-sm font-medium text-gray-900">{utilizationRate}%</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    {stats.ptoUsed} of {stats.totalPTO} days used
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Request Status Distribution */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Request Status</h3>
          <div className="space-y-3">
            {[
              { status: 'Approved', count: requests.filter(r => r.status === 'approved').length, color: 'green' },
              { status: 'Pending', count: requests.filter(r => r.status === 'pending').length, color: 'yellow' },
              { status: 'Denied', count: requests.filter(r => r.status === 'denied').length, color: 'red' }
            ].map(item => (
              <div key={item.status} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full bg-${item.color}-500`}></div>
                  <span className="text-sm text-gray-600">{item.status}</span>
                </div>
                <span className="font-medium text-gray-900">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* PTO Type Distribution */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">PTO Type Usage</h3>
          <div className="space-y-3">
            {[
              { type: 'Vacation', count: requests.filter(r => r.type === 'vacation').length, color: 'blue' },
              { type: 'Sick', count: requests.filter(r => r.type === 'sick').length, color: 'red' },
              { type: 'Personal', count: requests.filter(r => r.type === 'personal').length, color: 'green' }
            ].map(item => (
              <div key={item.type} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full bg-${item.color}-500`}></div>
                  <span className="text-sm text-gray-600">{item.type}</span>
                </div>
                <span className="font-medium text-gray-900">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Requests</span>
              <span className="font-medium text-gray-900">{requests.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Days Requested</span>
              <span className="font-medium text-gray-900">{requests.reduce((sum, r) => sum + r.days, 0)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Processing Time</span>
              <span className="font-medium text-gray-900">1.2 days</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Peak Month</span>
              <span className="font-medium text-gray-900">June</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};