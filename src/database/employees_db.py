from .database import Database
import sqlite3
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import secrets
from ..utils.password_utils import hash_password, verify_password
import os

class EmployeesDatabase(Database):
    def __init__(self, db_path=None):
        """Initialize database connection"""
        if db_path is None or db_path == ":memory:":
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(BASE_DIR, "data")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "employees.db")
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.create_tables()
        print("Connected to database")
        print("Database initialization complete")
        
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            print("بدء إعداد قاعدة البيانات...")
            
            # Start transaction
            self.conn.execute("BEGIN TRANSACTION")
            
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            print("إنشاء الجداول...")
            # Create tables if they don't exist
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS employees (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department_code TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    FOREIGN KEY (department_code) REFERENCES departments(code),
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                );

                CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id INTEGER,
                    permission_code TEXT,
                    PRIMARY KEY (role_id, permission_code),
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    FOREIGN KEY (permission_code) REFERENCES permissions(code)
                );

                CREATE TABLE IF NOT EXISTS user_passwords (
                    employee_id TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    reset_token TEXT,
                    reset_token_expires TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                );

                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL,
                    ip_address TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                );

                CREATE TABLE IF NOT EXISTS remember_me_tokens (
                    token TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (role_id) REFERENCES roles(id)
                );

                -- Create indices for better performance
                CREATE INDEX IF NOT EXISTS idx_employee_department ON employees(department_code);
                CREATE INDEX IF NOT EXISTS idx_employee_role ON employees(role_id);
                CREATE INDEX IF NOT EXISTS idx_login_attempts_employee ON login_attempts(employee_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_employee ON sessions(employee_id);
            """)
            
            print("تم إنشاء الجداول بنجاح")
            self.conn.commit()
            print("تم حفظ التغييرات")
            
        except sqlite3.Error as e:
            print(f"حدث خطأ أثناء إنشاء الجداول: {e}")
            self.conn.rollback()
            raise
            
    def setup_database(self):
        """This method is now handled by create_tables"""
        pass
        
    def get_all_departments(self) -> List[Dict]:
        """Get all departments"""
        cursor = self.conn.execute(
            """
            SELECT DISTINCT d.code, d.name
            FROM departments d
            ORDER BY d.name
            """)
        return [dict(row) for row in cursor.fetchall()]
        
    def get_all_employees(self) -> List[Dict]:
        """Get all employees with their department and role information"""
        cursor = self.conn.execute(
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
            """)
        return [dict(row) for row in cursor.fetchall()]
        
    def add_employee(self, employee_id: str, name: str, department_code: str, role_id: int) -> bool:
        """Add a new employee"""
        try:
            print(f"Adding new employee: ID={employee_id}, Name={name}, Department={department_code}, Role={role_id}")
            
            # Check if employee already exists
            cursor = self.conn.execute("SELECT 1 FROM employees WHERE id = ?", (employee_id,))
            if cursor.fetchone():
                print(f"Employee with ID {employee_id} already exists")
                return False
                
            # Check if department exists
            cursor = self.conn.execute("SELECT 1 FROM departments WHERE code = ?", (department_code,))
            if not cursor.fetchone():
                print(f"Department with code {department_code} does not exist")
                return False
                
            # Check if role exists
            cursor = self.conn.execute("SELECT 1 FROM roles WHERE id = ?", (role_id,))
            if not cursor.fetchone():
                print(f"Role with ID {role_id} does not exist")
                return False

            self.conn.execute(
                """
                INSERT INTO employees 
                (id, name, department_code, role_id)
                VALUES (?, ?, ?, ?)
                """,
                (employee_id, name, department_code, role_id)
            )
            self.conn.commit()
            print(f"Successfully added employee {name} with ID {employee_id}")
            return True
        except sqlite3.Error as e:
            print(f"Error adding employee: {e}")
            self.conn.rollback()
            return False
            
    def update_employee(self, employee_id: str, name: str, department_code: str, role_id: int) -> bool:
        """Update employee information"""
        try:
            self.conn.execute(
                """
                UPDATE employees 
                SET name = ?, department_code = ?, role_id = ?
                WHERE id = ?
                """,
                (name, department_code, role_id, employee_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            self.conn.rollback()
            return False
            
    def delete_employee(self, employee_id: str) -> bool:
        """Delete an employee"""
        try:
            self.conn.execute(
                "DELETE FROM employees WHERE id = ?",
                (employee_id,)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            self.conn.rollback()
            return False
            
    def get_employee(self, employee_id: str) -> dict:
        """Get employee information by ID."""
        cursor = self.conn.execute(
            """
            SELECT 
                e.id, e.name, e.department_code,
                d.name as department_name,
                r.name as role_name,
                e.role_id
            FROM employees e
            JOIN departments d ON e.department_code = d.code
            JOIN roles r ON e.role_id = r.id
            WHERE e.id = ?
            """,
            (employee_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'department_code': row[2],
                'department': row[3],
                'role': row[4],
                'role_id': row[5]
            }
        return None
        
    def get_next_employee_id(self) -> str:
        """
        Get the next available employee ID.
        Format: YYYYXXXX where YYYY is current year and XXXX is sequential number
        """
        try:
            current_year = str(datetime.now().year)
            
            # Get the highest ID for the current year
            cursor = self.conn.execute(
                "SELECT id FROM employees WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
                (f"{current_year}%",)
            )
            result = cursor.fetchone()
            
            if result:
                # Extract the sequential number and increment
                current_id = result[0]
                seq_num = int(current_id[4:]) + 1
            else:
                # Start with 0001 for the first employee of the year
                seq_num = 1
            
            # Format: YYYY0001, YYYY0002, etc.
            new_id = f"{current_year}{seq_num:04d}"
            return new_id
            
        except Exception as e:
            print(f"Error generating employee ID: {str(e)}")
            # If any error occurs, return a default format
            return f"{current_year}0001"

    def get_department_status(self, department_code: str, date: Optional[str] = None) -> List[Dict]:
        """Get current status for all employees in a department."""
        query = """
            SELECT 
                e.id as employee_id,
                e.name as employee_name,
                t.name as status_type,
                s.start_date,
                s.end_date,
                s.notes,
                s.approved,
                s.approved_by,
                a.name as approved_by_name,
                s.created_at,
                d.name as department_name
            FROM employees e
            JOIN employee_status s ON e.id = s.employee_id
            JOIN status_types t ON s.status_type_id = t.id
            LEFT JOIN employees a ON s.approved_by = a.id
            LEFT JOIN departments d ON e.department_code = d.code
            WHERE e.department_code = ?
        """
        params = [department_code]
        if date:
            query += " AND s.start_date <= ? AND (s.end_date >= ? OR s.end_date IS NULL)"
            params.extend([date, date])
        cursor = self.conn.execute(query, tuple(params))
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            results.append({
                'employee_id': row_dict.get('employee_id', ''),
                'employee_name': row_dict.get('employee_name', ''),
                'status_type': row_dict.get('status_type', ''),
                'start_date': row_dict.get('start_date', ''),
                'end_date': row_dict.get('end_date', ''),
                'notes': row_dict.get('notes', ''),
                'approved': bool(row_dict.get('approved', False)),
                'approved_by': row_dict.get('approved_by_name', '') if row_dict.get('approved_by') else '',
                'department': row_dict.get('department_name', ''),
                'created_at': row_dict.get('created_at', '')
            })
        return results

    def assign_employee_shift(
        self,
        employee_id: str,
        shift_type_id: int,
        start_date: str,
        end_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """تعيين وردية لموظف"""
        try:
            # التحقق من وجود الموظف
            cursor = self.conn.execute(
                "SELECT 1 FROM employees WHERE id = ?",
                (employee_id,)
            )
            if not cursor.fetchone():
                return False
                
            # التحقق من وجود الوردية
            cursor = self.conn.execute(
                "SELECT 1 FROM shift_types WHERE id = ?",
                (shift_type_id,)
            )
            if not cursor.fetchone():
                return False
                
            # إضافة الوردية للموظف
            self.conn.execute(
                """
                INSERT INTO employee_shifts 
                (employee_id, shift_type_id, start_date, end_date, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (employee_id, shift_type_id, start_date, end_date, notes)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            self.conn.rollback()
            return False

    def get_employee_shifts(
        self,
        employee_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict]:
        """جلب ورديات موظف معين"""
        query = """
            SELECT 
                s.id,
                t.name as shift_name,
                t.start_time,
                t.end_time,
                s.start_date,
                s.end_date,
                s.notes
            FROM employee_shifts s
            JOIN shift_types t ON s.shift_type_id = t.id
            WHERE s.employee_id = ?
        """
        params = [employee_id]
        
        if from_date:
            query += " AND (s.end_date >= ? OR s.end_date IS NULL)"
            params.append(from_date)
            
        if to_date:
            query += " AND s.start_date <= ?"
            params.append(to_date)
            
        query += " ORDER BY s.start_date DESC"
        
        cursor = self.conn.execute(query, tuple(params))
        return [{
            'id': row['id'],
            'shift_name': row['shift_name'],
            'shift_start': row['start_time'],
            'shift_end': row['end_time'],
            'start_date': row['start_date'],
            'end_date': row['end_date'],
            'notes': row['notes']
        } for row in cursor.fetchall()]

    def get_employee_status(
        self,
        employee_id: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict]:
        """جلب سجل حالات الموظف"""
        query = """
            SELECT 
                s.id,
                t.name as status_type,
                s.start_date,
                s.end_date,
                s.notes,
                s.approved,
                s.approved_by,
                e.name as approved_by_name,
                s.created_at,
                d.name as department
            FROM employee_status s
            JOIN status_types t ON s.status_type_id = t.id
            LEFT JOIN employees e ON s.approved_by = e.id
            LEFT JOIN employees emp ON s.employee_id = emp.id
            LEFT JOIN departments d ON emp.department_code = d.code
            WHERE s.employee_id = ?
        """
        params = [employee_id]
        
        if from_date:
            query += " AND (s.end_date >= ? OR s.end_date IS NULL)"
            params.append(from_date)
            
        if to_date:
            query += " AND s.start_date <= ?"
            params.append(to_date)
            
        query += " ORDER BY s.start_date DESC"
        
        cursor = self.conn.execute(query, tuple(params))
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # إضافة المفاتيح المطلوبة مع قيم افتراضية إذا كانت غير موجودة
            results.append({
                'id': row_dict['id'],
                'status_type': row_dict['status_type'],
                'start_date': row_dict['start_date'],
                'end_date': row_dict['end_date'],
                'notes': row_dict['notes'] or '',
                'approved': bool(row_dict['approved']),
                'approved_by': row_dict['approved_by'] or '',  # إضافة معرف الموظف الذي وافق
                'approved_by_name': row_dict['approved_by_name'] or '',  # إضافة اسم الموظف الذي وافق
                'department': row_dict['department'] or '',
                'created_at': row_dict['created_at']
            })
        return results

    def add_employee_status(
        self,
        employee_id: str,
        status_type_id: int,
        start_date: str,
        end_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """إضافة حالة جديدة لموظف"""
        try:
            # التحقق من وجود الموظف
            cursor = self.conn.execute(
                "SELECT 1 FROM employees WHERE id = ?",
                (employee_id,)
            )
            if not cursor.fetchone():
                print(f"Employee {employee_id} not found")
                return False
                
            # التحقق من نوع الحالة وجلب تفاصيلها
            cursor = self.conn.execute(
                "SELECT requires_approval, max_days FROM status_types WHERE id = ?",
                (status_type_id,)
            )
            status_type = cursor.fetchone()
            if not status_type:
                print(f"Status type {status_type_id} not found")
                return False
                
            requires_approval = status_type['requires_approval']
            
            # إذا كانت الحالة لا تتطلب موافقة، نوافق عليها تلقائياً
            approved = not requires_approval
            
            # إضافة سجل الحالة
            self.conn.execute(
                """
                INSERT INTO employee_status 
                (employee_id, status_type_id, start_date, end_date, notes, approved)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (employee_id, status_type_id, start_date, end_date, notes, approved)
            )
            
            self.conn.commit()
            print(f"Successfully added status for employee {employee_id}")
            return True
        except sqlite3.Error as e:
            print(f"Error in add_employee_status: {str(e)}")
            self.conn.rollback()
            return False

    def get_status_id(self, employee_id: str, start_date: str) -> Optional[int]:
        """جلب معرف الحالة لموظف وتاريخ معين"""
        try:
            cursor = self.conn.execute(
                """
                SELECT id
                FROM employee_status
                WHERE employee_id = ? AND start_date = ?
                """,
                (employee_id, start_date)
            )
            result = cursor.fetchone()
            return result['id'] if result else None
        except sqlite3.Error as e:
            print(f"Error in get_status_id: {str(e)}")
            return None

    def get_all_status(self, approved: Optional[bool] = None) -> List[Dict]:
        """Get all status records with optional approval filter."""
        query = """
            SELECT 
                s.id,
                e.id as employee_id,
                e.name as employee_name,
                t.name as status_type,
                s.start_date,
                s.end_date,
                s.notes,
                s.approved,
                s.approved_by,
                a.name as approved_by_name,
                s.created_at,
                d.name as department_name
            FROM employee_status s
            JOIN employees e ON s.employee_id = e.id
            JOIN status_types t ON s.status_type_id = t.id
            LEFT JOIN employees a ON s.approved_by = a.id
            LEFT JOIN departments d ON e.department_code = d.code
        """
        params = []
        
        if approved is not None:
            query += " WHERE s.approved = ?"
            params.append(approved)
            
        query += " ORDER BY s.start_date DESC"
        
        cursor = self.conn.execute(query, tuple(params))
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            results.append({
                'id': row_dict.get('id'),
                'employee_id': row_dict.get('employee_id', ''),
                'employee_name': row_dict.get('employee_name', ''),
                'status_type': row_dict.get('status_type', ''),
                'start_date': row_dict.get('start_date', ''),
                'end_date': row_dict.get('end_date', ''),
                'notes': row_dict.get('notes', ''),
                'approved': bool(row_dict.get('approved', False)),
                'approved_by': row_dict.get('approved_by_name', '') if row_dict.get('approved_by') else '',
                'department': row_dict.get('department_name', ''),
                'created_at': row_dict.get('created_at', '')
            })
        return results

    def set_user_password(self, employee_id: str, password: str) -> bool:
        """Set or update user password"""
        try:
            password_hash = hash_password(password)
            
            self.conn.execute(
                """
                INSERT OR REPLACE INTO user_passwords 
                (employee_id, password_hash, last_password_change, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (employee_id, password_hash)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            self.conn.rollback()
            return False

    def verify_password(self, employee_id: str, password: str) -> bool:
        """Verify user password"""
        try:
            cursor = self.conn.execute(
                """
                SELECT password_hash FROM user_passwords 
                WHERE employee_id = ?
                """,
                (employee_id,)
            )
            result = cursor.fetchone()
            if not result:
                return False
                
            return verify_password(result['password_hash'], password)
        except sqlite3.Error:
            return False

    def record_login_attempt(self, employee_id: str, success: bool, ip_address: Optional[str] = None) -> None:
        """Record a login attempt"""
        try:
            self.conn.execute(
                """
                INSERT INTO login_attempts 
                (employee_id, success, ip_address)
                VALUES (?, ?, ?)
                """,
                (employee_id, success, ip_address)
            )
            self.conn.commit()
        except sqlite3.Error:
            self.conn.rollback()

    def get_recent_login_attempts(self, employee_id: str, minutes: int = 30) -> int:
        """Get number of failed login attempts in the last X minutes"""
        try:
            cursor = self.conn.execute(
                """
                SELECT COUNT(*) as count
                FROM login_attempts
                WHERE employee_id = ?
                AND success = 0
                AND attempt_time > datetime('now', ?)
                """,
                (employee_id, f'-{minutes} minutes')
            )
            result = cursor.fetchone()
            return result['count'] if result else 0
        except sqlite3.Error:
            return 0

    def create_remember_me_token(self, employee_id: str, days: int = 30) -> Optional[str]:
        """Create a remember me token"""
        try:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=days)
            
            self.conn.execute(
                """
                INSERT INTO remember_me_tokens 
                (token, employee_id, expires_at)
                VALUES (?, ?, ?)
                """,
                (token, employee_id, expires_at.isoformat())
            )
            self.conn.commit()
            return token
        except sqlite3.Error:
            self.conn.rollback()
            return None

    def verify_remember_me_token(self, token: str) -> Optional[str]:
        """Verify a remember me token and return employee_id if valid"""
        try:
            cursor = self.conn.execute(
                """
                SELECT employee_id
                FROM remember_me_tokens
                WHERE token = ?
                AND expires_at > datetime('now')
                """,
                (token,)
            )
            result = cursor.fetchone()
            return result['employee_id'] if result else None
        except sqlite3.Error:
            return None

    def create_password_reset_token(self, employee_id: str, hours: int = 24) -> Optional[str]:
        """Create a password reset token"""
        try:
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=hours)
            
            self.conn.execute(
                """
                UPDATE user_passwords
                SET password_reset_token = ?,
                    password_reset_expiry = ?
                WHERE employee_id = ?
                """,
                (token, expiry.isoformat(), employee_id)
            )
            self.conn.commit()
            return token
        except sqlite3.Error:
            self.conn.rollback()
            return None

    def verify_reset_token(self, token: str) -> Optional[str]:
        """Verify a password reset token and return employee_id if valid"""
        try:
            cursor = self.conn.execute(
                """
                SELECT employee_id
                FROM user_passwords
                WHERE password_reset_token = ?
                AND password_reset_expiry > datetime('now')
                """,
                (token,)
            )
            result = cursor.fetchone()
            return result['employee_id'] if result else None
        except sqlite3.Error:
            return None

    def clear_reset_token(self, employee_id: str) -> None:
        """Clear the password reset token"""
        try:
            self.conn.execute(
                """
                UPDATE user_passwords
                SET password_reset_token = NULL,
                    password_reset_expiry = NULL
                WHERE employee_id = ?
                """,
                (employee_id,)
            )
            self.conn.commit()
        except sqlite3.Error:
            self.conn.rollback()

    def verify_password_only(self, password: str) -> Optional[tuple]:
        """
        Verify password and return (employee_id, role_code, role_id) if valid.
        This method is used for password-only authentication.
        """
        try:
            # Hash the provided password
            password_hash = hash_password(password)
            print(f"\nمحاولة تسجيل الدخول...")
            print(f"كلمة المرور المشفرة: {password_hash}")
            
            # First, check if this password hash exists
            cursor = self.conn.execute(
                """
                SELECT COUNT(*) as count
                FROM user_passwords
                WHERE password_hash = ?
                """,
                (password_hash,)
            )
            result = cursor.fetchone()
            if result['count'] == 0:
                print("لم يتم العثور على كلمة المرور في قاعدة البيانات")
                return None
                
            # Get user details
            cursor = self.conn.execute(
                """
                SELECT 
                    e.id,
                    e.name,
                    r.code as role_code,
                    r.id as role_id,
                    r.name as role_name
                FROM user_passwords up
                JOIN employees e ON up.employee_id = e.id
                JOIN roles r ON e.role_id = r.id
                WHERE up.password_hash = ?
                """,
                (password_hash,)
            )
            result = cursor.fetchone()
            if result:
                print(f"تم العثور على المستخدم:")
                print(f"- الاسم: {result['name']}")
                print(f"- الدور: {result['role_name']}")
                return (result['id'], result['role_code'], result['role_id'])
            
            print("لم يتم العثور على معلومات المستخدم")
            return None
            
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {str(e)}")
            return None
            
    def debug_admin_password(self):
        """Debug function to check admin password"""
        try:
            cursor = self.conn.execute(
                """
                SELECT 
                    e.id,
                    e.name,
                    up.password_hash,
                    r.name as role_name
                FROM employees e
                JOIN roles r ON e.role_id = r.id
                LEFT JOIN user_passwords up ON e.id = up.employee_id
                WHERE r.code = 'ADMIN'
                """)
            admin = cursor.fetchone()
            if admin:
                print("\nمعلومات حساب المدير:")
                print(f"- رقم الموظف: {admin['id']}")
                print(f"- الاسم: {admin['name']}")
                print(f"- الدور: {admin['role_name']}")
                if admin['password_hash']:
                    print("- تم تعيين كلمة المرور")
                    # Test default password
                    test_password = "Admin@2024"
                    test_hash = hash_password(test_password)
                    if test_hash == admin['password_hash']:
                        print("- كلمة المرور الافتراضية صحيحة")
                    else:
                        print("- كلمة المرور الافتراضية غير صحيحة")
                else:
                    print("- لم يتم تعيين كلمة المرور")
            else:
                print("\nلم يتم العثور على حساب المدير")
                
            # Check roles table
            cursor = self.conn.execute("SELECT * FROM roles")
            roles = cursor.fetchall()
            print("\nالأدوار المتوفرة:")
            for role in roles:
                print(f"- {role['name']} (code: {role['code']}, id: {role['id']})")
                
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {str(e)}")
            
    def reset_admin_password(self) -> bool:
        """Reset admin password to default"""
        try:
            # Get admin user
            cursor = self.conn.execute(
                """
                SELECT e.id
                FROM employees e
                JOIN roles r ON e.role_id = r.id
                WHERE r.code = 'ADMIN'
                """)
            admin = cursor.fetchone()
            if not admin:
                print("لم يتم العثور على حساب المدير")
                return False
                
            # Reset password
            admin_password = "Admin@2024"
            password_hash = hash_password(admin_password)
            
            self.conn.execute(
                """
                INSERT OR REPLACE INTO user_passwords 
                (employee_id, password_hash, last_password_change, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (admin['id'], password_hash)
            )
            self.conn.commit()
            
            print("\nتم إعادة تعيين كلمة مرور المدير")
            print(f"كلمة المرور الجديدة: {admin_password}")
            return True
            
        except sqlite3.Error as e:
            print(f"خطأ في قاعدة البيانات: {str(e)}")
            self.conn.rollback()
            return False

    def create_session(self, employee_id: str, role_id: int, hours: int = 12) -> Optional[str]:
        """Create a new session for the user"""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=hours)
            
            self.conn.execute(
                """
                INSERT INTO sessions 
                (id, employee_id, role_id, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, employee_id, role_id, expires_at.isoformat())
            )
            self.conn.commit()
            return session_id
        except sqlite3.Error:
            self.conn.rollback()
            return None

    def verify_session(self, session_id: str) -> Optional[tuple]:
        """Verify session and return (employee_id, role_code) if valid"""
        try:
            cursor = self.conn.execute(
                """
                SELECT 
                    s.employee_id,
                    r.code as role_code,
                    r.id as role_id
                FROM sessions s
                JOIN roles r ON s.role_id = r.id
                WHERE s.id = ?
                AND s.expires_at > datetime('now')
                """,
                (session_id,)
            )
            result = cursor.fetchone()
            if result:
                # Update last activity
                self.conn.execute(
                    """
                    UPDATE sessions
                    SET last_activity = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (session_id,)
                )
                self.conn.commit()
                return (result['employee_id'], result['role_code'])
            return None
        except sqlite3.Error:
            return None

    def end_session(self, session_id: str) -> bool:
        """End a session"""
        try:
            self.conn.execute(
                """
                DELETE FROM sessions
                WHERE id = ?
                """,
                (session_id,)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            self.conn.rollback()
            return False

    def get_user_permissions(self, role_id: int) -> List[str]:
        """Get list of permission codes for a role"""
        try:
            print(f"Getting permissions for role {role_id}")
            cursor = self.conn.execute(
                """
                SELECT DISTINCT p.code
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_code = p.code
                WHERE rp.role_id = ?
                ORDER BY p.code
                """,
                (role_id,)
            )
            permissions = [row['code'] for row in cursor.fetchall()]
            print(f"Found permissions: {permissions}")
            return permissions
        except sqlite3.Error as e:
            print(f"Error loading permissions: {str(e)}")
            return [] 