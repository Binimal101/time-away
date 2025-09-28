import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Calendar, Users } from 'lucide-react';
import { PTORequest, Employee } from '../types';
import { formatDate } from '../utils/dateUtils';

interface TeamCalendarProps {
  requests: PTORequest[];
  employees: Employee[];
}

export const TeamCalendar: React.FC<TeamCalendarProps> = ({ requests, employees }) => {
  const [currentDate, setCurrentDate] = useState(new Date());

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const formatMonthYear = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const newDate = new Date(prev);
      newDate.setMonth(prev.getMonth() + (direction === 'next' ? 1 : -1));
      return newDate;
    });
  };

  const getRequestsForDate = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    return requests.filter(request => {
      const start = new Date(request.startDate);
      const end = new Date(request.endDate);
      return date >= start && date <= end && request.status === 'approved';
    });
  };

  const generateCalendar = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const days = [];
    const today = new Date();

    // Empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-24 border border-gray-200"></div>);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
      const dayRequests = getRequestsForDate(date);
      const isToday = date.toDateString() === today.toDateString();
      const isPast = date < today;

      days.push(
        <div
          key={day}
          className={`h-24 border border-gray-200 p-1 ${
            isToday ? 'bg-blue-50 border-blue-300' : isPast ? 'bg-gray-50' : 'bg-white'
          }`}
        >
          <div className={`text-sm font-medium ${
            isToday ? 'text-blue-700' : isPast ? 'text-gray-400' : 'text-gray-900'
          }`}>
            {day}
          </div>
          <div className="mt-1 space-y-1">
            {dayRequests.slice(0, 2).map((request, index) => (
              <div
                key={`${request.id}-${index}`}
                className={`text-xs px-1 py-0.5 rounded truncate ${
                  request.type === 'vacation' ? 'bg-blue-100 text-blue-700' :
                  request.type === 'sick' ? 'bg-red-100 text-red-700' :
                  'bg-green-100 text-green-700'
                }`}
                title={`${request.employeeName} - ${request.type}`}
              >
                {request.employeeName}
              </div>
            ))}
            {dayRequests.length > 2 && (
              <div className="text-xs text-gray-500">+{dayRequests.length - 2} more</div>
            )}
          </div>
        </div>
      );
    }

    return days;
  };

  const upcomingRequests = requests
    .filter(request => {
      const startDate = new Date(request.startDate);
      const today = new Date();
      return startDate >= today && request.status === 'approved';
    })
    .sort((a, b) => new Date(a.startDate).getTime() - new Date(b.startDate).getTime())
    .slice(0, 5);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Team Calendar</h2>
          <p className="text-gray-600">View team availability and approved time off</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {/* Calendar Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <button
                onClick={() => navigateMonth('prev')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <h3 className="text-lg font-semibold text-gray-900">
                {formatMonthYear(currentDate)}
              </h3>
              <button
                onClick={() => navigateMonth('next')}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>

            {/* Calendar Grid */}
            <div className="p-4">
              <div className="grid grid-cols-7 gap-0 mb-2">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="p-2 text-center text-sm font-medium text-gray-500">
                    {day}
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-7 gap-0">
                {generateCalendar()}
              </div>
            </div>

            {/* Legend */}
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Legend</h4>
              <div className="flex space-x-4 text-xs">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-blue-100 rounded mr-1"></div>
                  Vacation
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-red-100 rounded mr-1"></div>
                  Sick Leave
                </div>
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-100 rounded mr-1"></div>
                  Personal
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Team Summary */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center mb-4">
              <Users className="h-5 w-5 text-gray-400 mr-2" />
              <h3 className="font-semibold text-gray-900">Team Summary</h3>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Employees</span>
                <span className="font-medium">{employees.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Out Today</span>
                <span className="font-medium">
                  {getRequestsForDate(new Date()).length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Pending Requests</span>
                <span className="font-medium">
                  {requests.filter(r => r.status === 'pending').length}
                </span>
              </div>
            </div>
          </div>

          {/* Upcoming Time Off */}
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center mb-4">
              <Calendar className="h-5 w-5 text-gray-400 mr-2" />
              <h3 className="font-semibold text-gray-900">Upcoming Time Off</h3>
            </div>
            {upcomingRequests.length === 0 ? (
              <p className="text-sm text-gray-500">No upcoming time off</p>
            ) : (
              <div className="space-y-3">
                {upcomingRequests.map(request => (
                  <div key={request.id} className="flex items-start space-x-3">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      request.type === 'vacation' ? 'bg-blue-500' :
                      request.type === 'sick' ? 'bg-red-500' : 'bg-green-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {request.employeeName}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatDate(request.startDate)} - {formatDate(request.endDate)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};