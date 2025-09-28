import React from 'react';
import { CheckCircle, XCircle, AlertCircle, Calendar, Clock, User, Filter } from 'lucide-react';
import { PTORequest } from '../types';
import { formatDate, formatDateTime } from '../utils/dateUtils';

interface RequestsListProps {
  requests: PTORequest[];
  showAllRequests?: boolean;
  onApprove?: (requestId: string) => void;
  onDeny?: (requestId: string, notes: string) => void;
}

export const RequestsList: React.FC<RequestsListProps> = ({
  requests,
  showAllRequests = false,
  onApprove,
  onDeny
}) => {
  const [filter, setFilter] = React.useState<'all' | 'pending' | 'approved' | 'denied'>('all');
  const [denyingRequest, setDenyingRequest] = React.useState<string | null>(null);
  const [denyNotes, setDenyNotes] = React.useState('');

  const filteredRequests = requests.filter(request => {
    if (filter === 'all') return true;
    return request.status === filter;
  });

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

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'vacation': return <Calendar className="h-4 w-4" />;
      case 'sick': return <Clock className="h-4 w-4" />;
      case 'personal': return <User className="h-4 w-4" />;
    }
  };

  const handleDenySubmit = (requestId: string) => {
    if (onDeny) {
      onDeny(requestId, denyNotes);
      setDenyingRequest(null);
      setDenyNotes('');
    }
  };

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex items-center space-x-4">
        <Filter className="h-5 w-5 text-gray-400" />
        <div className="flex space-x-2">
          {(['all', 'pending', 'approved', 'denied'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                filter === status
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Requests */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 divide-y divide-gray-200">
        {filteredRequests.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p>No requests found</p>
          </div>
        ) : (
          filteredRequests.map((request) => (
            <div key={request.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <div className="mt-1">
                    {getStatusIcon(request.status)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      {getTypeIcon(request.type)}
                      <h4 className="font-medium text-gray-900">
                        {showAllRequests && `${request.employeeName} - `}
                        {request.type.charAt(0).toUpperCase() + request.type.slice(1)} Leave
                      </h4>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {formatDate(request.startDate)} - {formatDate(request.endDate)} ({request.days} day{request.days !== 1 ? 's' : ''})
                    </p>
                    {request.reason && (
                      <p className="text-sm text-gray-500 mt-2">{request.reason}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-2">
                      Submitted {formatDateTime(request.submittedAt)}
                    </p>
                    {request.reviewedAt && (
                      <p className="text-xs text-gray-400">
                        Reviewed by {request.reviewedBy} on {formatDateTime(request.reviewedAt)}
                      </p>
                    )}
                    {request.managerNotes && (
                      <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                        <strong>Manager Notes:</strong> {request.managerNotes}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(request.status)}`}>
                    {request.status.charAt(0).toUpperCase() + request.status.slice(1)}
                  </span>

                  {request.status === 'pending' && onApprove && onDeny && (
                    <div className="flex space-x-2">
                      <button
                        onClick={() => onApprove(request.id)}
                        className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => setDenyingRequest(request.id)}
                        className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
                      >
                        Deny
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Deny Modal */}
              {denyingRequest === request.id && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                  <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Deny Request</h3>
                    <p className="text-gray-600 mb-4">
                      Please provide a reason for denying this request:
                    </p>
                    <textarea
                      value={denyNotes}
                      onChange={(e) => setDenyNotes(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Reason for denial..."
                    />
                    <div className="flex space-x-3 mt-4">
                      <button
                        onClick={() => {
                          setDenyingRequest(null);
                          setDenyNotes('');
                        }}
                        className="flex-1 py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleDenySubmit(request.id)}
                        className="flex-1 py-2 px-4 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                      >
                        Deny Request
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};