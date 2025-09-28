import React from 'react';
import { Users, TrendingUp, Calendar, AlertCircle } from 'lucide-react';
import { PTORequest, Employee, PTOBalance } from '../types';
import { RequestsList } from './RequestsList';

interface ManagerDashboardProps {
  teamRequests: PTORequest[];
  teamMembers: Employee[];
  teamBalances: PTOBalance[];
  onApprove: (requestId: string) => void;
  onDeny: (requestId: string, notes: string) => void;
}

export const ManagerDashboard: React.FC<ManagerDashboardProps> = ({
  teamRequests,
  teamMembers,
  teamBalances,
  onApprove,
  onDeny
}) => {
  const pendingRequests = teamRequests.filter(r => r.status === 'pending');
  const approvedThisMonth = teamRequests.filter(r => {
    const reviewedDate = r.reviewedAt ? new Date(r.reviewedAt) : null;
    const thisMonth = new Date();
    thisMonth.setDate(1);
    return r.status === 'approved' && reviewedDate && reviewedDate >= thisMonth;
  });

  const totalTeamPTO = teamBalances.reduce((sum, balance) => sum + balance.totalAvailable, 0);
  const totalUsedPTO = teamBalances.reduce((sum, balance) => sum + balance.totalUsed, 0);

  const stats = [
    {
      label: 'Pending Requests',
      value: pendingRequests.length,
      icon: AlertCircle,
      color: 'yellow',
      change: '+2 from last week'
    },
    {
      label: 'Team Members',
      value: teamMembers.length,
      icon: Users,
      color: 'blue',
      change: 'Active employees'
    },
    {
      label: 'Approved This Month',
      value: approvedThisMonth.length,
      icon: Calendar,
      color: 'green',
      change: `${approvedThisMonth.reduce((sum, r) => sum + r.days, 0)} days total`
    },
    {
      label: 'Team PTO Usage',
      value: `${Math.round((totalUsedPTO / (totalTeamPTO + totalUsedPTO)) * 100)}%`,
      icon: TrendingUp,
      color: 'purple',
      change: `${totalUsedPTO}/${totalTeamPTO + totalUsedPTO} days`
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Manager Dashboard</h2>
        <p className="text-gray-600">Manage your team's time off requests and view analytics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
                  <p className="text-xs text-gray-500 mt-1">{stat.change}</p>
                </div>
                <div className={`p-3 rounded-lg bg-${stat.color}-50`}>
                  <Icon className={`h-6 w-6 text-${stat.color}-600`} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Team Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Pending Requests</h3>
              <p className="text-sm text-gray-600">Review and approve team time off requests</p>
            </div>
            <div className="p-6">
              {pendingRequests.length === 0 ? (
                <div className="text-center py-8">
                  <AlertCircle className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No pending requests</p>
                </div>
              ) : (
                <RequestsList
                  requests={pendingRequests}
                  showAllRequests={true}
                  onApprove={onApprove}
                  onDeny={onDeny}
                />
              )}
            </div>
          </div>
        </div>

        {/* Team Members */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Team Members</h3>
          <div className="space-y-3">
            {teamMembers.map(member => {
              const balance = teamBalances.find(b => b.employeeId === member.id);
              const usagePercentage = balance 
                ? Math.round((balance.totalUsed / (balance.totalAvailable + balance.totalUsed)) * 100)
                : 0;

              return (
                <div key={member.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{member.name}</p>
                    <p className="text-sm text-gray-500">{member.department}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {balance?.totalAvailable || 0} days left
                    </p>
                    <p className="text-xs text-gray-500">{usagePercentage}% used</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* All Requests */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">All Team Requests</h3>
          <p className="text-sm text-gray-600">Complete history of team time off requests</p>
        </div>
        <div className="p-6">
          <RequestsList
            requests={teamRequests}
            showAllRequests={true}
            onApprove={onApprove}
            onDeny={onDeny}
          />
        </div>
      </div>
    </div>
  );
};