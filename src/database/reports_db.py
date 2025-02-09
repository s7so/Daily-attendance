from .database import Database
from datetime import datetime, timedelta
from typing import Optional, List, Dict

class ReportsDatabase(Database):
    def get_attendance_records(
        self,
        from_date: datetime,
        to_date: datetime,
        employee_id: Optional[str] = None,
        department_code: Optional[str] = None
    ) -> List[Dict]:
        """Get attendance records with optional filters."""
        query = """
            SELECT 
                a.date,
                e.id as employee_id,
                e.name as employee_name,
                d.name as department_name,
                r.name as role_name,
                a.check_in_time,
                a.check_out_time,
                CASE
                    WHEN a.check_out_time IS NOT NULL
                    THEN time(
                        (strftime('%s', a.check_out_time) - 
                         strftime('%s', a.check_in_time)) || ' seconds'
                    )
                    ELSE NULL
                END as work_hours
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            JOIN departments d ON e.department_code = d.code
            JOIN roles r ON e.role_id = r.id
            WHERE a.date BETWEEN ? AND ?
        """
        params = [from_date, to_date]
        
        if employee_id:
            query += " AND e.id = ?"
            params.append(employee_id)
            
        if department_code:
            query += " AND e.department_code = ?"
            params.append(department_code)
            
        query += " ORDER BY a.date DESC, a.check_in_time DESC"
        
        self.cursor.execute(query, params)
        return [
            {
                'date': row[0],
                'employee_id': row[1],
                'employee_name': row[2],
                'department': row[3],
                'role': row[4],
                'check_in_time': row[5],
                'check_out_time': row[6] or '',
                'work_hours': row[7] or ''
            }
            for row in self.cursor.fetchall()
        ]
        
    def get_department_summary(self, from_date: datetime, to_date: datetime) -> List[Dict]:
        """Get attendance summary by department."""
        self.cursor.execute(
            """
            SELECT 
                d.name as department_name,
                COUNT(DISTINCT e.id) as total_employees,
                COUNT(DISTINCT a.employee_id) as present_employees,
                AVG(
                    CASE 
                        WHEN a.check_out_time IS NOT NULL 
                        THEN (strftime('%s', a.check_out_time) - 
                              strftime('%s', a.check_in_time))/3600.0 
                        ELSE NULL 
                    END
                ) as avg_hours
            FROM departments d
            LEFT JOIN employees e ON d.code = e.department_code
            LEFT JOIN attendance a ON e.id = a.employee_id 
                AND a.date BETWEEN ? AND ?
            GROUP BY d.code, d.name
            ORDER BY d.name
            """,
            (from_date, to_date)
        )
        return [
            {
                'department': row[0],
                'total_employees': row[1],
                'present_employees': row[2],
                'average_hours': round(row[3] or 0, 2)
            }
            for row in self.cursor.fetchall()
        ]
        
    def get_employee_summary(self, employee_id: str, from_date: datetime, to_date: datetime) -> Dict:
        """Get attendance summary for a specific employee."""
        self.cursor.execute(
            """
            SELECT 
                e.name,
                d.name as department_name,
                r.name as role_name,
                COUNT(a.id) as total_days,
                AVG(
                    CASE 
                        WHEN a.check_out_time IS NOT NULL 
                        THEN (strftime('%s', a.check_out_time) - 
                              strftime('%s', a.check_in_time))/3600.0 
                        ELSE NULL 
                    END
                ) as avg_hours,
                MIN(a.check_in_time) as earliest_check_in,
                MAX(a.check_out_time) as latest_check_out
            FROM employees e
            JOIN departments d ON e.department_code = d.code
            JOIN roles r ON e.role_id = r.id
            LEFT JOIN attendance a ON e.id = a.employee_id 
                AND a.date BETWEEN ? AND ?
            WHERE e.id = ?
            GROUP BY e.id
            """,
            (from_date, to_date, employee_id)
        )
        row = self.cursor.fetchone()
        if row:
            return {
                'name': row[0],
                'department': row[1],
                'role': row[2],
                'total_days': row[3],
                'average_hours': round(row[4] or 0, 2),
                'earliest_check_in': row[5],
                'latest_check_out': row[6]
            }
        return None
        
    def get_all_departments(self) -> List[Dict]:
        """Get all departments for filtering."""
        self.cursor.execute(
            """
            SELECT code, name 
            FROM departments 
            ORDER BY name
            """
        )
        return [
            {
                'code': row[0],
                'name': row[1]
            }
            for row in self.cursor.fetchall()
        ]
        
    def get_all_employees(self) -> List[Dict]:
        """Get all employees with their department and role information"""
        cursor = self.execute_query(
            """
            SELECT 
                e.id,
                e.name,
                d.name as department_name,
                r.name as role_name,
                e.department_code,
                e.role_id
            FROM employees e
            LEFT JOIN departments d ON e.department_code = d.code
            LEFT JOIN roles r ON e.role_id = r.id
            ORDER BY e.name
            """
        )
        return [dict(row) for row in cursor.fetchall()]
        
    def get_late_arrivals(self, date: datetime, threshold_time: str = '09:00:00') -> List[Dict]:
        """Get employees who arrived late on a specific date."""
        self.cursor.execute(
            """
            SELECT 
                e.name,
                d.name as department_name,
                a.check_in_time
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            JOIN departments d ON e.department_code = d.code
            WHERE a.date = ?
            AND time(a.check_in_time) > time(?)
            ORDER BY a.check_in_time
            """,
            (date, threshold_time)
        )
        return [
            {
                'name': row[0],
                'department': row[1],
                'check_in_time': row[2]
            }
            for row in self.cursor.fetchall()
        ]
        
    def get_overtime_report(self, date: datetime, regular_hours: float = 8.0) -> List[Dict]:
        """Get employees who worked overtime on a specific date."""
        self.cursor.execute(
            """
            SELECT 
                e.name,
                d.name as department_name,
                a.check_in_time,
                a.check_out_time,
                (strftime('%s', a.check_out_time) - 
                 strftime('%s', a.check_in_time))/3600.0 as hours_worked
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            JOIN departments d ON e.department_code = d.code
            WHERE a.date = ?
            AND a.check_out_time IS NOT NULL
            AND (strftime('%s', a.check_out_time) - 
                 strftime('%s', a.check_in_time))/3600.0 > ?
            ORDER BY hours_worked DESC
            """,
            (date, regular_hours)
        )
        return [
            {
                'name': row[0],
                'department': row[1],
                'check_in': row[2],
                'check_out': row[3],
                'hours_worked': round(row[4], 2)
            }
            for row in self.cursor.fetchall()
        ] 