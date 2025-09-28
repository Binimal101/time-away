import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, X, Bot, User, CheckCircle, XCircle, AlertTriangle, Users, Calendar } from 'lucide-react';
import { Employee, PTORequest, Task, Department, Skill } from '../types';
import { formatDate } from '../utils/dateUtils';
import { tasks, departments, skills } from '../data/mockData';

interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface ChatBotProps {
  employees: Employee[];
  requests: PTORequest[];
  onApprove: (requestId: string) => void;
  onDeny: (requestId: string, notes: string) => void;
  currentUser: Employee;
}

export default function ChatBot({ employees, requests, onApprove, onDeny, currentUser }: ChatBotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      content: "Hi! I'm your AI PTO Assistant. I can help you analyze team availability, review pending requests, and make informed decisions about time off approvals. What would you like to know?",
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const analyzeTeamAvailability = (startDate: string, endDate: string, department: string) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    // Get employees in the same department
    const deptEmployees = employees.filter(emp => 
      emp.department === department && emp.role === 'employee'
    );
    
    // Check for overlapping requests
    const overlappingRequests = requests.filter(req => {
      if (req.status !== 'approved') return false;
      
      const reqStart = new Date(req.startDate);
      const reqEnd = new Date(req.endDate);
      
      return (start <= reqEnd && end >= reqStart);
    });
    
    const unavailableEmployees = overlappingRequests.map(req => req.employeeName);
    const availableEmployees = deptEmployees.filter(emp => 
      !unavailableEmployees.includes(emp.name)
    );
    
    // Get department info
    const dept = departments.find(d => d.name === department);
    const minStaffing = dept?.minStaffingLevel || 1;
    const criticalSkills = dept?.criticalSkills || [];
    
    // Check critical skill coverage
    const skillCoverage = criticalSkills.map(skill => {
      const employeesWithSkill = availableEmployees.filter(emp => 
        emp.skills.includes(skill)
      );
      return {
        skill,
        available: employeesWithSkill.length,
        employees: employeesWithSkill.map(emp => emp.name)
      };
    });
    
    return {
      totalEmployees: deptEmployees.length,
      availableEmployees: availableEmployees.length,
      unavailableEmployees: unavailableEmployees.length,
      availableNames: availableEmployees.map(emp => emp.name),
      unavailableNames: unavailableEmployees,
      coverageRatio: availableEmployees.length / deptEmployees.length,
      minStaffing,
      meetsMinStaffing: availableEmployees.length >= minStaffing,
      skillCoverage,
      criticalSkillsAtRisk: skillCoverage.filter(sc => sc.available === 0).map(sc => sc.skill)
    };
  };

  const generateRecommendation = (request: PTORequest) => {
    const employee = employees.find(emp => emp.id === request.employeeId);
    if (!employee) return null;

    const availability = analyzeTeamAvailability(
      request.startDate, 
      request.endDate, 
      employee.department
    );

    // Check if employee has critical tasks during the period
    const employeeTasks = tasks.filter(task => {
      const taskStart = new Date(task.startDate);
      const taskEnd = new Date(task.endDate);
      const reqStart = new Date(request.startDate);
      const reqEnd = new Date(request.endDate);
      
      return task.assignedEmployeeId === employee.id &&
             task.status === 'in-progress' &&
             (reqStart <= taskEnd && reqEnd >= taskStart);
    });
    
    const criticalTasks = employeeTasks.filter(task => 
      task.priority === 'critical' || task.priority === 'high'
    );

    let recommendation = '';
    let status: 'approve' | 'deny' | 'caution' = 'approve';
    let reasoning = '';

    // Check multiple factors for recommendation
    const hasSkillCoverage = availability.criticalSkillsAtRisk.length === 0;
    const hasCriticalTasks = criticalTasks.length > 0;
    const meetsStaffing = availability.meetsMinStaffing;
    
    if (availability.coverageRatio >= 0.7 && hasSkillCoverage && meetsStaffing && !hasCriticalTasks) {
      recommendation = 'APPROVE';
      status = 'approve';
      reasoning = `✅ Strong team coverage with all critical skills covered. No high-priority tasks affected.`;
    } else if (availability.coverageRatio >= 0.5 && meetsStaffing) {
      recommendation = 'APPROVE WITH CAUTION';
      status = 'caution';
      let cautionReasons = [];
      if (!hasSkillCoverage) cautionReasons.push(`Critical skills at risk: ${availability.criticalSkillsAtRisk.join(', ')}`);
      if (hasCriticalTasks) cautionReasons.push(`${criticalTasks.length} critical task(s) affected`);
      reasoning = `⚠️ Moderate coverage. ${cautionReasons.join('. ')}.`;
    } else {
      recommendation = 'CONSIDER DENYING';
      status = 'deny';
      let denyReasons = [];
      if (!meetsStaffing) denyReasons.push(`Below minimum staffing (${availability.availableEmployees}/${availability.minStaffing})`);
      if (!hasSkillCoverage) denyReasons.push(`Critical skills unavailable: ${availability.criticalSkillsAtRisk.join(', ')}`);
      if (hasCriticalTasks) denyReasons.push(`${criticalTasks.length} critical task(s) at risk`);
      reasoning = `❌ ${denyReasons.join('. ')}.`;
    }

    return {
      recommendation,
      status,
      reasoning,
      availability,
      employee,
      criticalTasks,
      skillsAtRisk: availability.criticalSkillsAtRisk
    };
  };

  const processMessage = async (message: string) => {
    const lowerMessage = message.toLowerCase();
    let response = '';

    if (lowerMessage.includes('pending') || lowerMessage.includes('requests')) {
      const pendingRequests = requests.filter(req => req.status === 'pending');
      
      if (pendingRequests.length === 0) {
        response = "Great news! 🎉 You have no pending PTO requests to review right now.";
      } else {
        response = `I found ${pendingRequests.length} pending PTO request${pendingRequests.length > 1 ? 's' : ''} that need your attention:\n\n`;
        
        pendingRequests.forEach((request, index) => {
          const analysis = generateRecommendation(request);
          if (analysis) {
            const icon = analysis.status === 'approve' ? '✅' : analysis.status === 'caution' ? '⚠️' : '❌';
            response += `${icon} **${analysis.employee.name}** (${analysis.employee.department})\n`;
            response += `👔 ${analysis.employee.jobTitle} - ${analysis.employee.level} level\n`;
            response += `🛠️ Skills: ${analysis.employee.skills.slice(0, 3).join(', ')}${analysis.employee.skills.length > 3 ? '...' : ''}\n`;
            response += `📅 ${formatDate(request.startDate)} - ${formatDate(request.endDate)} (${request.days} days)\n`;
            response += `💼 ${request.type.charAt(0).toUpperCase() + request.type.slice(1)} - ${request.reason}\n`;
            response += `🤖 **${analysis.recommendation}**\n`;
            response += `📊 ${analysis.reasoning}\n`;
            
            if (analysis.criticalTasks.length > 0) {
              response += `⚠️ Critical tasks affected: ${analysis.criticalTasks.map(t => t.title).join(', ')}\n`;
            }
            
            if (analysis.skillsAtRisk.length > 0) {
              response += `🚨 Skills at risk: ${analysis.skillsAtRisk.join(', ')}\n`;
            }
            
            if (analysis.availability.availableNames.length > 0) {
              response += `👥 Available for coverage: ${analysis.availability.availableNames.slice(0, 3).join(', ')}${analysis.availability.availableNames.length > 3 ? '...' : ''}\n`;
            }
            response += '\n';
          }
        });
      }
    } else if (lowerMessage.includes('team') || lowerMessage.includes('availability')) {
      response = "Here's your current team availability by department:\n\n";
      
      const uniqueDepartments = [...new Set(employees.filter(emp => emp.role === 'employee').map(emp => emp.department))];
      
      uniqueDepartments.forEach(dept => {
        const deptEmployees = employees.filter(emp => emp.department === dept && emp.role === 'employee');
        const deptInfo = departments.find(d => d.name === dept);
        const currentlyOut = requests.filter(req => {
          const today = new Date();
          const start = new Date(req.startDate);
          const end = new Date(req.endDate);
          const employee = employees.find(emp => emp.id === req.employeeId);
          return req.status === 'approved' && 
                 employee?.department === dept && 
                 today >= start && today <= end;
        });
        
        const available = deptEmployees.length - currentlyOut.length;
        const minStaffing = deptInfo?.minStaffingLevel || 1;
        const statusIcon = available >= minStaffing ? '✅' : '⚠️';
        
        response += `${statusIcon} **${dept}**: ${available}/${deptEmployees.length} available (min: ${minStaffing})\n`;
        
        if (deptInfo?.criticalSkills) {
          const availableSkills = deptInfo.criticalSkills.filter(skill => {
            return deptEmployees.some(emp => 
              emp.skills.includes(skill) && 
              !currentlyOut.some(req => req.employeeId === emp.id)
            );
          });
          response += `   🛠️ Critical skills covered: ${availableSkills.length}/${deptInfo.criticalSkills.length}\n`;
        }
        
        if (currentlyOut.length > 0) {
          response += `   Currently out: ${currentlyOut.map(req => req.employeeName).join(', ')}\n`;
        }
        response += '\n';
      });
    } else if (lowerMessage.includes('skills') || lowerMessage.includes('coverage')) {
      response = "Here's the current skill coverage across your team:\n\n";
      
      const allCriticalSkills = [...new Set(departments.flatMap(d => d.criticalSkills || []))];
      
      allCriticalSkills.forEach(skill => {
        const employeesWithSkill = employees.filter(emp => 
          emp.skills.includes(skill) && emp.role === 'employee'
        );
        const currentlyAvailable = employeesWithSkill.filter(emp => {
          const isOut = requests.some(req => {
            const today = new Date();
            const start = new Date(req.startDate);
            const end = new Date(req.endDate);
            return req.employeeId === emp.id && 
                   req.status === 'approved' && 
                   today >= start && today <= end;
          });
          return !isOut;
        });
        
        const riskLevel = currentlyAvailable.length === 0 ? '🚨' : 
                         currentlyAvailable.length === 1 ? '⚠️' : '✅';
        
        response += `${riskLevel} **${skill}**: ${currentlyAvailable.length}/${employeesWithSkill.length} available\n`;
        if (currentlyAvailable.length > 0) {
          response += `   Available: ${currentlyAvailable.map(emp => `${emp.name} (${emp.level})`).join(', ')}\n`;
        }
        response += '\n';
      });
    } else if (lowerMessage.includes('tasks') || lowerMessage.includes('projects')) {
      const activeTasks = tasks.filter(task => task.status === 'in-progress' || task.status === 'pending');
      const criticalTasks = activeTasks.filter(task => task.priority === 'critical' || task.priority === 'high');
      
      response = `Current active tasks overview:\n\n`;
      response += `📊 **Summary**: ${activeTasks.length} active tasks (${criticalTasks.length} critical/high priority)\n\n`;
      
      criticalTasks.forEach(task => {
        const assignee = employees.find(emp => emp.id === task.assignedEmployeeId);
        const priorityIcon = task.priority === 'critical' ? '🚨' : '⚠️';
        
        response += `${priorityIcon} **${task.title}** (${task.priority})\n`;
        response += `   👤 Assigned: ${assignee?.name} (${assignee?.department})\n`;
        response += `   📅 ${formatDate(task.startDate)} - ${formatDate(task.endDate)}\n`;
        response += `   🛠️ Skills: ${task.requiredSkills.join(', ')}\n\n`;
      });
    } else if (lowerMessage.includes('help') || lowerMessage.includes('what can you do')) {
      response = `I'm your AI PTO Assistant! Here's what I can help you with:

🔍 **"Show me pending requests"** - Analyze all pending PTO requests with recommendations
📊 **"Team availability"** - Check current team availability across departments  
🛠️ **"Skills coverage"** - View critical skill availability across teams
📋 **"Active tasks"** - See current high-priority projects and assignments
👥 **"Coverage for [employee name]"** - Analyze coverage for specific requests
📅 **"Who's out next week?"** - See upcoming time off
⚡ **Quick Actions** - I can help you approve or deny requests with reasoning

I analyze team workload, skill coverage, critical tasks, and business impact to help you make informed decisions. Just ask me anything about your team's PTO!`;
    } else if (lowerMessage.includes('approve') || lowerMessage.includes('deny')) {
      response = "I can help you with approvals! To make the best decision, please ask me to 'show pending requests' first, and I'll provide detailed recommendations for each one.";
    } else {
      response = `I understand you're asking about: "${message}". 

I specialize in intelligent PTO management with skill and task analysis. Try asking me:
• "Show me pending requests"
• "What's my team availability?"  
• "Skills coverage analysis"
• "Show me critical tasks"
• "Help me decide on [employee name]'s request"
• "Who's out this week?"

How can I help you manage your team's time off more effectively?`;
    }

    return response;
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Simulate AI processing time
    setTimeout(async () => {
      const response = await processMessage(inputMessage);
      const botMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        content: response,
        sender: 'bot',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-full shadow-lg transition-all duration-200 z-50"
      >
        <MessageCircle className="h-6 w-6" />
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-lg shadow-2xl border border-gray-200 flex flex-col z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-blue-600 text-white rounded-t-lg">
            <div className="flex items-center space-x-2">
              <Bot className="h-5 w-5" />
              <span className="font-semibold">AI PTO Assistant</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white hover:text-gray-200 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {message.sender === 'bot' && (
                      <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    )}
                    {message.sender === 'user' && (
                      <User className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="whitespace-pre-wrap text-sm">
                      {message.content}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-800 p-3 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Bot className="h-4 w-4" />
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions */}
          {messages.length <= 1 && (
            <div className="px-4 py-2 border-t border-gray-200">
              <p className="text-xs text-gray-500 mb-2">Quick suggestions:</p>
              <div className="flex flex-wrap gap-1 mt-2">
                {['Show pending requests', 'Team availability', 'Skills coverage', 'Help'].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about PTO requests..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim()}
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}