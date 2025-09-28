import React, { useState } from 'react';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { RequestForm } from './components/RequestForm';
import { RequestsList } from './components/RequestsList';
import { TeamCalendar } from './components/TeamCalendar';
import { ManagerDashboard } from './components/ManagerDashboard';
import { Analytics } from './components/Analytics';
import { PolicyManagement } from './components/PolicyManagement';
import { TeamManagement } from './components/TeamManagement';
import ChatBot from './components/ChatBot';
import { employees as initialEmployees, ptoBalances, ptoRequests, currentUser } from './data/mockData';
import { PTORequest, Employee } from './types';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [requests, setRequests] = useState<PTORequest[]>(ptoRequests);
  const [employees, setEmployees] = useState<Employee[]>(initialEmployees);

  const handleNewRequest = (requestData: Omit<PTORequest, 'id' | 'employeeName' | 'submittedAt' | 'status'>) => {
    const employee = employees.find(emp => emp.id === requestData.employeeId);
    if (!employee) return;

    const newRequest: PTORequest = {
      ...requestData,
      id: Date.now().toString(),
      employeeName: employee.name,
      submittedAt: new Date().toISOString(),
      status: 'pending'
    };

    setRequests(prev => [newRequest, ...prev]);
  };

  const handleApprove = (requestId: string) => {
    setRequests(prev => prev.map(req => 
      req.id === requestId 
        ? { 
            ...req, 
            status: 'approved' as const,
            reviewedAt: new Date().toISOString(),
            reviewedBy: currentUser.name
          }
        : req
    ));
  };

  const handleDeny = (requestId: string, notes: string) => {
    setRequests(prev => prev.map(req => 
      req.id === requestId 
        ? { 
            ...req, 
            status: 'denied' as const,
            reviewedAt: new Date().toISOString(),
            reviewedBy: currentUser.name,
            managerNotes: notes
          }
        : req
    ));
  };

  const handleUpdateEmployee = (updatedEmployee: Employee) => {
    setEmployees(prev => prev.map(emp => 
      emp.id === updatedEmployee.id ? updatedEmployee : emp
    ));
  };

  const handleAddEmployee = (newEmployeeData: Omit<Employee, 'id'>) => {
    const newEmployee: Employee = {
      ...newEmployeeData,
      id: Date.now().toString()
    };
    setEmployees(prev => [...prev, newEmployee]);
  };

  const handleDeleteEmployee = (employeeId: string) => {
    setEmployees(prev => prev.filter(emp => emp.id !== employeeId));
  };

  const userRequests = requests.filter(req => req.employeeId === currentUser.id);
  const recentRequests = userRequests.slice(0, 5);
  const userBalance = ptoBalances.find(balance => balance.employeeId === currentUser.id);

  const teamMembers = currentUser.role === 'manager' 
    ? employees.filter(emp => emp.managerId === currentUser.id || emp.role === 'employee')
    : [];
  
  const teamRequests = currentUser.role === 'manager'
    ? requests.filter(req => {
        const employee = employees.find(emp => emp.id === req.employeeId);
        return employee && (employee.managerId === currentUser.id || employee.role === 'employee');
      })
    : [];

  const teamBalances = currentUser.role === 'manager'
    ? ptoBalances.filter(balance => {
        const employee = employees.find(emp => emp.id === balance.employeeId);
        return employee && (employee.managerId === currentUser.id || employee.role === 'employee');
      })
    : [];

  const renderContent = () => {
    switch (activeView) {
      case 'dashboard':
        return currentUser.role === 'manager' ? (
          <ManagerDashboard
            teamRequests={teamRequests}
            teamMembers={teamMembers}
            teamBalances={teamBalances}
            onApprove={handleApprove}
            onDeny={handleDeny}
          />
        ) : (
          <Dashboard
            balance={userBalance!}
            recentRequests={recentRequests}
            onNewRequest={() => setShowRequestForm(true)}
          />
        );
      case 'requests':
        return <RequestsList requests={userRequests} />;
      case 'calendar':
        return <TeamCalendar requests={requests} employees={employees} />;
      case 'manage':
        return (
          <ManagerDashboard
            teamRequests={teamRequests}
            teamMembers={teamMembers}
            teamBalances={teamBalances}
            onApprove={handleApprove}
            onDeny={handleDeny}
          />
        );
      case 'team':
        return (
          <TeamManagement
            employees={employees}
            balances={ptoBalances}
            onUpdateEmployee={handleUpdateEmployee}
            onAddEmployee={handleAddEmployee}
            onDeleteEmployee={handleDeleteEmployee}
          />
        );
      case 'analytics':
        return <Analytics requests={requests} employees={employees} balances={ptoBalances} />;
      case 'policies':
        return <PolicyManagement />;
      default:
        return null;
    }
  };

  return (
    <div className="App">
      <Layout
        activeView={activeView}
        onViewChange={setActiveView}
        currentUser={currentUser}
      >
        {renderContent()}
      </Layout>

      {showRequestForm && (
        <RequestForm
          onClose={() => setShowRequestForm(false)}
          onSubmit={handleNewRequest}
          currentUser={currentUser}
        />
      )}

      {currentUser.role === 'manager' && (
        <ChatBot
          employees={employees}
          requests={requests}
          onApprove={handleApprove}
          onDeny={handleDeny}
          currentUser={currentUser}
        />
      )}
    </div>
  );
}

export default App;