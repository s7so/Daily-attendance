from .database import Database
import sqlite3
from datetime import datetime, date

class AttendanceDatabase(Database):
    def record_check_in(self, employee_id: str) -> bool:
        """Record employee check-in time."""
        try:
            # Check if employee exists
            self.cursor.execute(
                "SELECT id FROM employees WHERE id = ?",
                (employee_id,)
            )
            if not self.cursor.fetchone():
                return False
                
            # Check if already checked in today
            today = date.today()
            self.cursor.execute(
                """
                SELECT id FROM attendance 
                WHERE employee_id = ? AND date = ? AND check_in_time IS NOT NULL
                """,
                (employee_id, today)
            )
            if self.cursor.fetchone():
                return False
                
            # Record check-in
            current_time = datetime.now().strftime('%H:%M:%S')
            self.cursor.execute(
                """
                INSERT INTO attendance (employee_id, date, check_in_time)
                VALUES (?, ?, ?)
                """,
                (employee_id, today, current_time)
            )
            self.connection.commit()
            return True
        except sqlite3.Error:
            return False
            
    def record_check_out(self, employee_id: str) -> bool:
        """Record employee check-out time."""
        try:
            today = date.today()
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Update the latest attendance record for today
            self.cursor.execute(
                """
                UPDATE attendance 
                SET check_out_time = ?
                WHERE employee_id = ? 
                AND date = ? 
                AND check_in_time IS NOT NULL 
                AND check_out_time IS NULL
                """,
                (current_time, employee_id, today)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False
            
    def get_today_attendance(self) -> list:
        """Get all attendance records for today."""
        today = date.today()
        self.cursor.execute(
            """
            SELECT 
                a.date,
                e.id,
                e.name,
                d.name as department_name,
                a.check_in_time,
                a.check_out_time
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            JOIN departments d ON e.department_code = d.code
            WHERE a.date = ?
            ORDER BY a.check_in_time DESC
            """,
            (today,)
        )
        
        return [
            {
                'date': row[0],
                'employee_id': row[1],
                'employee_name': row[2],
                'department': row[3],
                'check_in_time': row[4],
                'check_out_time': row[5] or ''
            }
            for row in self.cursor.fetchall()
        ] 