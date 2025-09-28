import React from 'react';
import { Calendar, Users, FileText, BarChart3, Settings, LogOut, Bell, TrendingUp, Zap } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeView: string;
  onViewChange: (view: string) => void;
  currentUser: any;
}

export const Layout: React.FC<LayoutProps> = ({ children, activeView, onViewChange, currentUser }) => {
  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    ...(currentUser.role === 'employee' ? [
      { id: 'requests', label: 'My Requests', icon: FileText }
    ] : []),
    { id: 'calendar', label: 'Team Calendar', icon: Calendar },
    ...(currentUser.role === 'manager' ? [
      { id: 'manage', label: 'Manage Team', icon: Users },
      { id: 'team', label: 'Team Management', icon: Users },
      { id: 'analytics', label: 'Analytics', icon: TrendingUp }
    ] : [])
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-md relative">
                  <div className="relative">
                    <Calendar className="h-5 w-5 text-white" />
                    <Zap className="h-3 w-3 text-yellow-300 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                  </div>
                </div>
              </div>
              <div className="ml-3">
                <h1 className="text-xl font-semibold text-gray-900">TimeAway</h1>
                <p className="text-sm text-gray-500">Automated Time Off Management System</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                <Bell className="h-5 w-5" />
              </button>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">{currentUser.name}</p>
                <p className="text-xs text-gray-500 capitalize">{currentUser.role} • {currentUser.department}</p>
              </div>
              <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                <Settings className="h-5 w-5" />
              </button>
              <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-sm min-h-screen sticky top-0">
          <div className="p-4 space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => onViewChange(item.id)}
                  className={`w-full flex items-center px-3 py-2 text-left rounded-lg transition-colors ${
                    activeView === item.id
                      ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-600 shadow-sm'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.label}
                </button>
              );
            })}
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <div className="max-w-6xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};