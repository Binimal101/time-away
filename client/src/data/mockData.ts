import { Employee, PTOBalance, PTORequest, Department, Task, Skill } from '../types';

export const skills: Skill[] = [
  { id: '1', name: 'React', category: 'Frontend', description: 'React.js development' },
  { id: '2', name: 'Node.js', category: 'Backend', description: 'Server-side JavaScript' },
  { id: '3', name: 'Python', category: 'Backend', description: 'Python programming' },
  { id: '4', name: 'AWS', category: 'Cloud', description: 'Amazon Web Services' },
  { id: '5', name: 'Docker', category: 'DevOps', description: 'Containerization' },
  { id: '6', name: 'SQL', category: 'Database', description: 'Database management' },
  { id: '7', name: 'UI/UX Design', category: 'Design', description: 'User interface design' },
  { id: '8', name: 'Project Management', category: 'Management', description: 'Project coordination' },
  { id: '9', name: 'Data Analysis', category: 'Analytics', description: 'Data analysis and reporting' },
  { id: '10', name: 'Marketing Strategy', category: 'Marketing', description: 'Strategic marketing planning' },
  { id: '11', name: 'Sales', category: 'Sales', description: 'Sales and customer relations' },
  { id: '12', name: 'HR Policies', category: 'HR', description: 'Human resources management' },
  { id: '13', name: 'Financial Analysis', category: 'Finance', description: 'Financial planning and analysis' },
  { id: '14', name: 'Java', category: 'Backend', description: 'Java programming' },
  { id: '15', name: 'Machine Learning', category: 'AI', description: 'ML algorithms and models' }
];

export const departments: Department[] = [
  {
    id: '1',
    name: 'Engineering',
    description: 'Software development and technical infrastructure',
    managerId: '3',
    criticalSkills: ['React', 'Node.js', 'Python', 'AWS', 'Docker'],
    minStaffingLevel: 3
  },
  {
    id: '2',
    name: 'Marketing',
    description: 'Brand management and customer acquisition',
    managerId: '3',
    criticalSkills: ['Marketing Strategy', 'UI/UX Design', 'Data Analysis'],
    minStaffingLevel: 2
  },
  {
    id: '3',
    name: 'Sales',
    description: 'Revenue generation and client relationships',
    managerId: '3',
    criticalSkills: ['Sales', 'Project Management'],
    minStaffingLevel: 2
  },
  {
    id: '4',
    name: 'HR',
    description: 'Human resources and employee relations',
    managerId: '3',
    criticalSkills: ['HR Policies', 'Project Management'],
    minStaffingLevel: 1
  },
  {
    id: '5',
    name: 'Finance',
    description: 'Financial planning and accounting',
    managerId: '3',
    criticalSkills: ['Financial Analysis', 'Data Analysis'],
    minStaffingLevel: 1
  }
];

export const employees: Employee[] = [
  { 
    id: '1', 
    name: 'John Smith', 
    email: 'john.smith@company.com', 
    role: 'employee', 
    department: 'Engineering', 
    jobTitle: 'Senior Full Stack Developer',
    skills: ['React', 'Node.js', 'AWS', 'Docker', 'SQL'],
    level: 'senior',
    managerId: '3' 
  },
  { 
    id: '2', 
    name: 'Sarah Johnson', 
    email: 'sarah.johnson@company.com', 
    role: 'employee', 
    department: 'Marketing', 
    jobTitle: 'Marketing Manager',
    skills: ['Marketing Strategy', 'UI/UX Design', 'Data Analysis', 'Project Management'],
    level: 'senior',
    managerId: '3' 
  },
  { 
    id: '3', 
    name: 'Mike Wilson', 
    email: 'mike.wilson@company.com', 
    role: 'manager', 
    department: 'Engineering',
    jobTitle: 'Engineering Director',
    skills: ['Project Management', 'React', 'Node.js', 'AWS', 'Python'],
    level: 'lead'
  },
  { 
    id: '4', 
    name: 'Emily Davis', 
    email: 'emily.davis@company.com', 
    role: 'employee', 
    department: 'HR', 
    jobTitle: 'HR Specialist',
    skills: ['HR Policies', 'Project Management', 'Data Analysis'],
    level: 'mid',
    managerId: '3' 
  },
  { 
    id: '5', 
    name: 'David Brown', 
    email: 'david.brown@company.com', 
    role: 'employee', 
    department: 'Engineering', 
    jobTitle: 'Backend Developer',
    skills: ['Python', 'Node.js', 'SQL', 'AWS', 'Docker'],
    level: 'mid',
    managerId: '3' 
  },
  { 
    id: '6', 
    name: 'Lisa Chen', 
    email: 'lisa.chen@company.com', 
    role: 'employee', 
    department: 'Marketing', 
    jobTitle: 'Digital Marketing Specialist',
    skills: ['Marketing Strategy', 'Data Analysis', 'UI/UX Design'],
    level: 'junior',
    managerId: '3' 
  },
  { 
    id: '7', 
    name: 'Robert Taylor', 
    email: 'robert.taylor@company.com', 
    role: 'employee', 
    department: 'Sales', 
    jobTitle: 'Sales Representative',
    skills: ['Sales', 'Project Management', 'Data Analysis'],
    level: 'mid',
    managerId: '3' 
  },
  { 
    id: '8', 
    name: 'Jennifer White', 
    email: 'jennifer.white@company.com', 
    role: 'employee', 
    department: 'HR', 
    jobTitle: 'HR Coordinator',
    skills: ['HR Policies', 'Data Analysis'],
    level: 'junior',
    managerId: '3' 
  },
];

export const tasks: Task[] = [
  {
    id: '1',
    title: 'Implement User Authentication',
    description: 'Build secure login and registration system',
    departmentId: '1',
    assignedEmployeeId: '1',
    requiredSkills: ['React', 'Node.js', 'SQL'],
    priority: 'high',
    startDate: '2025-02-01',
    endDate: '2025-02-15',
    status: 'in-progress'
  },
  {
    id: '2',
    title: 'Q1 Marketing Campaign',
    description: 'Launch new product marketing campaign',
    departmentId: '2',
    assignedEmployeeId: '2',
    requiredSkills: ['Marketing Strategy', 'UI/UX Design'],
    priority: 'critical',
    startDate: '2025-02-10',
    endDate: '2025-03-31',
    status: 'in-progress'
  },
  {
    id: '3',
    title: 'Database Migration',
    description: 'Migrate legacy database to new infrastructure',
    departmentId: '1',
    assignedEmployeeId: '5',
    requiredSkills: ['SQL', 'Python', 'AWS'],
    priority: 'high',
    startDate: '2025-02-20',
    endDate: '2025-03-10',
    status: 'pending'
  },
  {
    id: '4',
    title: 'Employee Onboarding Process',
    description: 'Streamline new employee onboarding',
    departmentId: '4',
    assignedEmployeeId: '4',
    requiredSkills: ['HR Policies', 'Project Management'],
    priority: 'medium',
    startDate: '2025-02-15',
    endDate: '2025-03-15',
    status: 'in-progress'
  },
  {
    id: '5',
    title: 'Sales Pipeline Optimization',
    description: 'Improve sales conversion rates',
    departmentId: '3',
    assignedEmployeeId: '7',
    requiredSkills: ['Sales', 'Data Analysis'],
    priority: 'high',
    startDate: '2025-02-05',
    endDate: '2025-02-25',
    status: 'in-progress'
  },
  {
    id: '6',
    title: 'API Development',
    description: 'Build REST API for mobile app',
    departmentId: '1',
    assignedEmployeeId: '1',
    requiredSkills: ['Node.js', 'SQL', 'AWS'],
    priority: 'critical',
    startDate: '2025-02-16',
    endDate: '2025-03-05',
    status: 'pending'
  }
];

// Set current user as manager for demo
export const currentUser: Employee = employees.find(emp => emp.role === 'manager') || employees[0];

export const ptoBalances: PTOBalance[] = [
  { 
    id: '1', employeeId: '1', year: 2025, vacationDays: 20, sickDays: 10, personalDays: 5, 
    usedVacation: 3, usedSick: 1, usedPersonal: 0,
    vacation: 17, sick: 9, personal: 5, totalAvailable: 35, totalUsed: 4
  },
  { 
    id: '2', employeeId: '2', year: 2025, vacationDays: 18, sickDays: 10, personalDays: 5, 
    usedVacation: 5, usedSick: 2, usedPersonal: 1,
    vacation: 13, sick: 8, personal: 4, totalAvailable: 33, totalUsed: 8
  },
  { 
    id: '3', employeeId: '3', year: 2025, vacationDays: 25, sickDays: 12, personalDays: 7, 
    usedVacation: 8, usedSick: 0, usedPersonal: 2,
    vacation: 17, sick: 12, personal: 5, totalAvailable: 44, totalUsed: 10
  },
  { 
    id: '4', employeeId: '4', year: 2025, vacationDays: 15, sickDays: 10, personalDays: 5, 
    usedVacation: 2, usedSick: 3, usedPersonal: 0,
    vacation: 13, sick: 7, personal: 5, totalAvailable: 30, totalUsed: 5
  },
  { 
    id: '5', employeeId: '5', year: 2025, vacationDays: 18, sickDays: 10, personalDays: 5, 
    usedVacation: 4, usedSick: 1, usedPersonal: 1,
    vacation: 14, sick: 9, personal: 4, totalAvailable: 33, totalUsed: 6
  },
  { 
    id: '6', employeeId: '6', year: 2025, vacationDays: 12, sickDays: 8, personalDays: 3, 
    usedVacation: 1, usedSick: 0, usedPersonal: 0,
    vacation: 11, sick: 8, personal: 3, totalAvailable: 22, totalUsed: 1
  },
  { 
    id: '7', employeeId: '7', year: 2025, vacationDays: 16, sickDays: 10, personalDays: 5, 
    usedVacation: 3, usedSick: 2, usedPersonal: 1,
    vacation: 13, sick: 8, personal: 4, totalAvailable: 31, totalUsed: 6
  },
  { 
    id: '8', employeeId: '8', year: 2025, vacationDays: 10, sickDays: 8, personalDays: 3, 
    usedVacation: 0, usedSick: 1, usedPersonal: 0,
    vacation: 10, sick: 7, personal: 3, totalAvailable: 21, totalUsed: 1
  }
];

export const ptoRequests: PTORequest[] = [
  {
    id: '1',
    employeeId: '1',
    employeeName: 'John Smith',
    type: 'vacation',
    startDate: '2025-02-15',
    endDate: '2025-02-17',
    reason: 'Family vacation to Florida',
    status: 'pending',
    submittedAt: '2025-01-20T10:00:00Z',
    days: 3
  },
  {
    id: '2',
    employeeId: '2',
    employeeName: 'Sarah Johnson',
    type: 'sick',
    startDate: '2025-02-10',
    endDate: '2025-02-10',
    reason: 'Doctor appointment',
    status: 'approved',
    submittedAt: '2025-01-18T14:30:00Z',
    approvedAt: '2025-01-19T09:15:00Z',
    reviewedAt: '2025-01-19T09:15:00Z',
    reviewedBy: 'Mike Wilson',
    days: 1
  },
  {
    id: '3',
    employeeId: '5',
    employeeName: 'David Brown',
    type: 'vacation',
    startDate: '2025-03-01',
    endDate: '2025-03-05',
    reason: 'Spring break trip',
    status: 'pending',
    submittedAt: '2025-01-22T16:45:00Z',
    days: 5
  },
  {
    id: '4',
    employeeId: '7',
    employeeName: 'Robert Taylor',
    type: 'personal',
    startDate: '2025-02-20',
    endDate: '2025-02-20',
    reason: 'Personal matters',
    status: 'approved',
    submittedAt: '2025-01-15T11:20:00Z',
    approvedAt: '2025-01-16T08:30:00Z',
    reviewedAt: '2025-01-16T08:30:00Z',
    reviewedBy: 'Mike Wilson',
    days: 1
  }
];