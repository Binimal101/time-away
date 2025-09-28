export interface Employee {
  id: string;
  name: string;
  email: string;
  role: 'employee' | 'manager';
  department: string;
  jobTitle: string;
  skills: string[];
  level: 'junior' | 'mid' | 'senior' | 'lead';
  managerId?: string;
}

export interface Department {
  id: string;
  name: string;
  description: string;
  managerId: string;
  criticalSkills: string[];
  minStaffingLevel: number;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  departmentId: string;
  assignedEmployeeId: string;
  requiredSkills: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  startDate: string;
  endDate: string;
  status: 'pending' | 'in-progress' | 'completed' | 'blocked';
}

export interface Skill {
  id: string;
  name: string;
  category: string;
  description: string;
}

export interface PTOBalance {
  id: string;
  employeeId: string;
  year: number;
  vacationDays: number;
  sickDays: number;
  personalDays: number;
  usedVacation: number;
  usedSick: number;
  usedPersonal: number;
  // Computed properties
  vacation: number;
  sick: number;
  personal: number;
  totalAvailable: number;
  totalUsed: number;
}

export interface PTORequest {
  id: string;
  employeeId: string;
  employeeName?: string;
  type: 'vacation' | 'sick' | 'personal';
  startDate: string;
  endDate: string;
  reason: string;
  status: 'pending' | 'approved' | 'denied';
  submittedAt: string;
  approvedAt?: string;
  reviewedAt?: string;
  reviewedBy?: string;
  managerNotes?: string;
  days?: number;
}