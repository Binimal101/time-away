@@ .. @@
 export interface Employee {
   id: string;
   name: string;
   email: string;
   role: 'employee' | 'manager';
   department: string;
+  jobTitle: string;
+  skills: string[];
+  level: 'junior' | 'mid' | 'senior' | 'lead';
   managerId?: string;
 }
 
+export interface Department {
+  id: string;
+  name: string;
+  description: string;
+  managerId: string;
+  criticalSkills: string[];
+  minStaffingLevel: number;
+}
+
+export interface Task {
+  id: string;
+  title: string;
+  description: string;
+  departmentId: string;
+  assignedEmployeeId: string;
+  requiredSkills: string[];
+  priority: 'low' | 'medium' | 'high' | 'critical';
+  startDate: string;
+  endDate: string;
+  status: 'pending' | 'in-progress' | 'completed' | 'blocked';
+}
+
+export interface Skill {
+  id: string;
+  name: string;
+  category: string;
+  descr
}iption: string;
+}
+
 export interface PTOBalance {