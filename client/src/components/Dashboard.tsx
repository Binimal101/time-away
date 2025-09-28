import React from 'react';
import { Calendar, Clock, TrendingUp, Users, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { PTOBalance, PTORequest } from '../types';
import { formatDate } from '../utils/dateUtils';

interface DashboardProps {
  balance: PTOBalance;
  recentRequests: PTORequest[];
  onNewRequest: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ balance, recentRequests, onNewRequest }) => {
  const balanceCards = [
    { label: 'Vacation Days', value: balance.vacation, color: 'blue', icon: Calendar },
    { label: 'Sick Days', value: balance.sick, color: 'red', icon: Clock },
    { label: 'Personal Days', value: balance.personal, color: 'green', icon: Users },
    { label: 'Total Available', value: balance.totalAvailable, color: 'purple', icon: TrendingUp }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'denied': return <XCircle className="h-5 w-5 text-red-500" />;
      default: return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return 'text-green-700 bg-green-50';
      case 'denied': return 'text-red-700 bg-red-50';
      default: return 'text-yellow-700 bg-yellow-50';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-gray-600">Manage your time off requests and view your balances</p>
        </div>
        <button
          onClick={onNewRequest}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          Request Time Off
        </button>
      </div>

      {/* Balance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {balanceCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} className="bg-white rounded-lg p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg bg-${card.color}-50`}>
                  <Icon className={`h-6 w-6 text-${card.color}-600`} />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{card.label}</p>
                  <p className="text-2xl font-bold text-gray-900">{card.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Usage Overview */}
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">PTO Usage Overview</h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Total Used</span>
              <span>{balance.totalUsed} / {balance.totalAvailable + balance.totalUsed} days</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                style={{ width: `${(balance.totalUsed / (balance.totalAvailable + balance.totalUsed)) * 100}%` }}
              ></div>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{balance.vacation}</p>
              <p className="text-sm text-gray-600">Vacation</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{balance.sick}</p>
              <p className="text-sm text-gray-600">Sick</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{balance.personal}</p>
              <p className="text-sm text-gray-600">Personal</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Requests */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Recent Requests</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {recentRequests.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p>No recent requests</p>
            </div>
          ) : (
            recentRequests.map((request) => (
              <div key={request.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(request.status)}
                      <div>
                        <p className="font-medium text-gray-900 capitalize">
                          {request.type} - {request.days} day{request.days !== 1 ? 's' : ''}
                        </p>
                        <p className="text-sm text-gray-600">
                          {formatDate(request.startDate)} - {formatDate(request.endDate)}
                        </p>
                        {request.reason && (
                          <p className="text-sm text-gray-500 mt-1">{request.reason}</p>
                        )}
                      </div>
                    </div>
                  </div>
                  <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(request.status)}`}>
                    {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};