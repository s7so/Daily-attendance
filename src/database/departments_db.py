from .database import Database
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import secrets
import os


class DepartmentsDatabase(Database):
    def __init__(self, db_path=None):
        """تهيئة قاعدة البيانات"""
        # إذا متمش تمرير مسار قاعدة بيانات أو لو كان ":memory:"، استخدم مسار ثابت في مجلد "data"
        if db_path is None or db_path == ":memory:":
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(BASE_DIR, "data")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "departments.db")
        self.db_path = db_path
        # استخدام check_same_thread=False لتجنب مشاكل الـ threading
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection = self.conn
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        # تفعيل الـ WAL mode لتحسين الأداء والموثوقية
        self.conn.execute("PRAGMA journal_mode=WAL;")
        # تفعيل المزامنة الفورية للبيانات
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.create_tables()
        self.update_database_schema()  # تحديث هيكل قاعدة البيانات عند التهيئة
        self.initialize_default_departments()
        self.initialize_default_roles()  # إضافة استدعاء الدالة الجديدة
        self.initialize_default_users()  # إضافة استدعاء الدالة الجديدة
        self.initialize_default_shifts()  # إضافة استدعاء الدالة الجديدة

    def __del__(self):
        """التأكد من إغلاق الاتصال عند حذف الكائن"""
        self.close()

    def commit(self):
        """حفظ التغييرات في قاعدة البيانات"""
        try:
            self.conn.commit()
            print("Changes committed successfully")
        except Exception as e:
            print(f"Error committing changes: {e}")
            self.rollback()
            raise

    def rollback(self):
        """التراجع عن التغييرات"""
        try:
            self.conn.rollback()
            print("Changes rolled back")
        except Exception as e:
            print(f"Error rolling back changes: {e}")
            raise

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.conn:
            try:
                self.commit()  # محاولة حفظ أي تغييرات معلقة
                self.conn.close()
                self.conn = None
                print("Database connection closed successfully")
            except Exception as e:
                print(f"Error closing database connection: {e}")
                raise

    def create_tables(self):
        """تهيئة قاعدة البيانات وإنشاء الجداول"""
        try:
            # بدء المعاملة
            self.conn.execute("BEGIN TRANSACTION")

            # إنشاء الجداول
            self.conn.executescript("""
                -- جدول إصدارات قاعدة البيانات
                CREATE TABLE IF NOT EXISTS db_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- جدول تذكرني
                CREATE TABLE IF NOT EXISTS remember_me_tokens (
                    token TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    device_info TEXT,
                    ip_address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                );

                -- إنشاء مؤشر للبحث السريع
                CREATE INDEX IF NOT EXISTS idx_remember_me_employee ON remember_me_tokens(employee_id);
                CREATE INDEX IF NOT EXISTS idx_remember_me_expires ON remember_me_tokens(expires_at);
                
                -- إنشاء جدول الأقسام
                CREATE TABLE IF NOT EXISTS departments (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent_code TEXT,
                    FOREIGN KEY (parent_code) REFERENCES departments(code)
                );

                -- إنشاء جدول الأدوار
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    code TEXT NOT NULL UNIQUE
                );

                -- إنشاء جدول الصلاحيات
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT
                );

                -- إنشاء جدول أجهزة البصمة
                CREATE TABLE IF NOT EXISTS fingerprint_devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    model TEXT,
                    ip_address TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    location TEXT,
                    status TEXT DEFAULT 'active',
                    last_sync TIMESTAMP
                );

                -- إنشاء جدول سجل نقل الموظفين بين الأقسام
                CREATE TABLE IF NOT EXISTS department_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    old_department_code TEXT NOT NULL,
                    new_department_code TEXT NOT NULL,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (old_department_code) REFERENCES departments(code),
                    FOREIGN KEY (new_department_code) REFERENCES departments(code)
                );

                -- إنشاء جدول الحضور والانصراف
                DROP TABLE IF EXISTS attendance;
                CREATE TABLE attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    check_in_time TIME,
                    check_out_time TIME,
                    source TEXT DEFAULT 'manual',
                    device_id TEXT,
                    status TEXT DEFAULT 'present',
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (device_id) REFERENCES fingerprint_devices(id),
                    UNIQUE(employee_id, date)
                );

                -- إنشاء جدول أنواع الحالات
                CREATE TABLE IF NOT EXISTS status_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    requires_approval BOOLEAN DEFAULT TRUE,
                    max_days INTEGER DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- إنشاء جدول حالات الموظفين
                CREATE TABLE IF NOT EXISTS employee_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    status_type_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    notes TEXT,
                    approved BOOLEAN DEFAULT FALSE,
                    approved_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (status_type_id) REFERENCES status_types(id),
                    FOREIGN KEY (approved_by) REFERENCES employees(id)
                );

                -- إنشاء جدول الورديات
                CREATE TABLE IF NOT EXISTS shift_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    break_duration INTEGER DEFAULT 60,
                    flexible_minutes INTEGER DEFAULT 0,
                    overtime_allowed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- إنشاء جدول ورديات الموظفين
                CREATE TABLE IF NOT EXISTS employee_shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    shift_type_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id)
                );

                -- إنشاء المؤشرات
                CREATE INDEX IF NOT EXISTS idx_attendance_employee ON attendance(employee_id);
                CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
                CREATE INDEX IF NOT EXISTS idx_attendance_device ON attendance(device_id);
                CREATE INDEX IF NOT EXISTS idx_emp_shifts ON employee_shifts(employee_id);
                CREATE INDEX IF NOT EXISTS idx_shift_dates ON employee_shifts(start_date, end_date);
                CREATE INDEX IF NOT EXISTS idx_emp_status ON employee_status(employee_id);
                CREATE INDEX IF NOT EXISTS idx_status_dates ON employee_status(start_date, end_date);
                CREATE INDEX IF NOT EXISTS idx_department_history_employee ON department_history(employee_id);
                CREATE INDEX IF NOT EXISTS idx_department_history_old ON department_history(old_department_code);
                CREATE INDEX IF NOT EXISTS idx_department_history_new ON department_history(new_department_code);

                -- إدخال أنواع الحالات الافتراضية
                INSERT OR IGNORE INTO status_types (name, requires_approval, max_days) VALUES 
                    ('إجازة سنوية', TRUE, 21),
                    ('إجازة مرضية', TRUE, 30),
                    ('مأمورية', TRUE, NULL),
                    ('انتداب', TRUE, NULL),
                    ('عمل عن بعد', TRUE, NULL),
                    ('حضور', FALSE, NULL);
            """)

            # تحديث إصدار قاعدة البيانات
            self.conn.execute("""
                INSERT OR REPLACE INTO db_version (version) VALUES (1)
            """)

            # حفظ التغييرات
            self.conn.commit()
            print("Database schema created successfully")

        except sqlite3.Error as e:
            print(f"Error creating tables: {str(e)}")
            self.conn.rollback()
            raise

    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        return self.conn

    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """تنفيذ استعلام SQL"""
        conn = self.get_connection()
        return conn.execute(query, params)

    def execute_query_with_commit(self, query: str, params: tuple = ()) -> bool:
        """تنفيذ استعلام SQL مع حفظ التغييرات"""
        try:
            conn = self.get_connection()
            conn.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error:
            return False

    def get_status_types(self) -> List[Dict]:
        """جلب جميع أنواع الحالات"""
        cursor = self.execute_query(
            """
            SELECT 
                id,
                name,
                requires_approval,
                max_days
            FROM status_types
            ORDER BY name
            """
        )
        return [
            {
                'id': row['id'],
                'name': row['name'],
                'requires_approval': bool(row['requires_approval']),
                'max_days': row['max_days']
            }
            for row in cursor.fetchall()
        ]

    def get_available_managers(self) -> List[Dict]:
        """جلب قائمة الموظفين المؤهلين ليكونوا مدراء"""
        try:
            cursor = self.execute_query(
                """
                SELECT 
                    e.id,
                    e.name,
                    d.name as current_department,
                    CASE 
                        WHEN dm.code IS NOT NULL THEN 1 
                        ELSE 0 
                    END as is_manager
                FROM employees e
                JOIN roles r ON e.role_id = r.id
                LEFT JOIN departments d ON e.department_code = d.code
                LEFT JOIN departments dm ON dm.manager_id = e.id
                WHERE r.name = 'مدير'
                ORDER BY e.name
                """
            )
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error getting available managers: {e}")
            return []

    def add_department(self, code: str, name: str, manager_id: Optional[str] = None) -> bool:
        """إضافة قسم جديد"""
        try:
            print(f"Adding new department: Code={code}, Name={name}, Manager ID={manager_id}")

            # التحقق من عدم وجود القسم
            cursor = self.execute_query(
                "SELECT 1 FROM departments WHERE code = ?",
                (code,)
            )
            if cursor.fetchone():
                print(f"Department with code {code} already exists")
                return False

            # التحقق من وجود المدير وصلاحياته إذا تم تحديده
            if manager_id:
                cursor = self.execute_query(
                    """
                    SELECT 1 FROM employees e
                    JOIN roles r ON e.role_id = r.id
                    WHERE e.id = ? AND r.name = 'مدير'
                    """,
                    (manager_id,)
                )
                if not cursor.fetchone():
                    print(f"Employee {manager_id} is not a manager")
                    return False

            # إضافة القسم
            self.execute_query(
                "INSERT INTO departments (code, name, manager_id) VALUES (?, ?, ?)",
                (code, name, manager_id)
            )

            self.commit()
            print(f"Successfully added department {name} with code {code}")
            return True

        except sqlite3.Error as e:
            print(f"Error adding department: {e}")
            self.rollback()
            return False

    def update_department(self, code: str, name: str, manager_id: Optional[str] = None) -> bool:
        """تحديث معلومات قسم"""
        try:
            print(f"Updating department: Code={code}, Name={name}, Manager ID={manager_id}")

            # التحقق من وجود القسم
            cursor = self.execute_query(
                "SELECT 1 FROM departments WHERE code = ?",
                (code,)
            )
            if not cursor.fetchone():
                print(f"Department with code {code} does not exist")
                return False

            # التحقق من وجود المدير وصلاحياته إذا تم تحديده
            if manager_id:
                cursor = self.execute_query(
                    """
                    SELECT 1 FROM employees e
                    JOIN roles r ON e.role_id = r.id
                    WHERE e.id = ? AND r.name = 'مدير'
                    """,
                    (manager_id,)
                )
                if not cursor.fetchone():
                    print(f"Employee {manager_id} is not a manager")
                    return False

            # تحديث معلومات القسم
            self.execute_query(
                "UPDATE departments SET name = ?, manager_id = ? WHERE code = ?",
                (name, manager_id, code)
            )

            self.commit()
            print(f"Successfully updated department {name}")
            return True

        except sqlite3.Error as e:
            print(f"Error updating department: {e}")
            self.rollback()
            return False

    def get_department(self, code: str) -> Optional[Dict]:
        """جلب معلومات قسم معين"""
        try:
            cursor = self.execute_query(
                """
                SELECT 
                    d.code, 
                    d.name, 
                    d.manager_id, 
                    e.name as manager_name,
                    (SELECT COUNT(*) FROM employees WHERE department_code = d.code) as employee_count
                FROM departments d
                LEFT JOIN employees e ON d.manager_id = e.id
                WHERE d.code = ?
                """,
                (code,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'code': row['code'],
                    'name': row['name'],
                    'manager_id': row['manager_id'],
                    'manager_name': row['manager_name'],
                    'employee_count': row['employee_count']
                }
            return None

        except sqlite3.Error as e:
            print(f"Error getting department: {e}")
            return None

    def get_all_departments(self) -> List[Dict]:
        """جلب جميع الأقسام"""
        cursor = self.execute_query("""
                SELECT 
                    d.code, 
                    d.name, 
                    d.manager_id,
                    e.name as manager_name
                FROM departments d
                LEFT JOIN employees e ON d.manager_id = e.id
                ORDER BY d.name
            """)
        return [dict(row) for row in cursor.fetchall()]

    def get_department_employees(self, code: str) -> List[Dict]:
        """جلب موظفي قسم معين"""
        cursor = self.execute_query(
            """
            SELECT 
                e.id, 
                e.name,
                COALESCE(r.name, 'موظف') as role,
                COALESCE(r.id, 1) as role_id
            FROM employees e
            LEFT JOIN roles r ON e.role_id = r.id
            WHERE e.department_code = ?
            ORDER BY e.name
            """,
            (code,)
        )
        employees = [dict(row) for row in cursor.fetchall()]
        print(f"Found {len(employees)} employees for department {code}")
        return employees

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

    def transfer_employee(self, employee_id: str, new_department_code: str) -> bool:
        """نقل موظف إلى قسم آخر"""
        try:
            # التحقق من وجود الموظف والقسم الجديد
            cursor = self.execute_query(
                """
                SELECT e.department_code as current_dept
                FROM employees e
                WHERE e.id = ?
                """,
                (employee_id,)
            )
            employee = cursor.fetchone()
            if not employee:
                print(f"Employee {employee_id} not found")
                return False

            cursor = self.execute_query(
                "SELECT 1 FROM departments WHERE code = ?",
                (new_department_code,)
            )
            if not cursor.fetchone():
                print(f"Department {new_department_code} not found")
                return False

            # بدء المعاملة
            self.conn.execute("BEGIN TRANSACTION")

            # تحديث القسم
            self.execute_query(
                """
                UPDATE employees 
                SET department_code = ?
                WHERE id = ?
                """,
                (new_department_code, employee_id)
            )

            # تسجيل التغيير في سجل النقل
            self.execute_query(
                """
                INSERT INTO department_history 
                (employee_id, old_department_code, new_department_code)
                VALUES (?, ?, ?)
                """,
                (employee_id, employee['current_dept'], new_department_code)
            )

            # حفظ التغييرات
            self.conn.commit()
            print(f"Successfully transferred employee {employee_id} to department {new_department_code}")
            return True

        except sqlite3.Error as e:
            print(f"Error transferring employee: {str(e)}")
            self.conn.rollback()
            return False

    def get_employee_department_history(self, employee_id: str) -> List[Dict]:
        """جلب سجل نقل الموظف بين الأقسام"""
        cursor = self.execute_query(
            """
            SELECT 
                h.changed_at,
                d_old.name as old_department,
                d_new.name as new_department
            FROM department_history h
            JOIN departments d_old ON h.old_department_code = d_old.code
            JOIN departments d_new ON h.new_department_code = d_new.code
            WHERE h.employee_id = ?
            ORDER BY h.changed_at DESC
            """,
            (employee_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_roles(self):
        """الحصول على قائمة الأدوار الوظيفية"""
        query = "SELECT id, name FROM roles ORDER BY id"
        cursor = self.execute_query(query)
        return [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]

    def get_managers(self) -> List[Dict]:
        """جلب جميع الموظفين الذين لديهم دور مدير"""
        cursor = self.execute_query(
            """
            SELECT 
                e.id, 
                e.name,
                d.name as department_name
            FROM employees e
            JOIN roles r ON e.role_id = r.id
            JOIN departments d ON e.department_code = d.code
            WHERE r.name = 'مدير'
            ORDER BY e.name
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_role(self, name: str) -> bool:
        """إضافة دور وظيفي جديد"""
        try:
            conn = self.get_connection()
            conn.execute(
                "INSERT INTO roles (name) VALUES (?)",
                (name,)
            )
            self.commit()
            return True
        except sqlite3.Error:
            self.rollback()
            return False

    def update_role(self, old_name: str, new_name: str) -> bool:
        """تحديث اسم الدور الوظيفي"""
        try:
            self.execute_query(
                "UPDATE roles SET name = ? WHERE name = ?",
                (new_name, old_name)
            )
            self.commit()
            return True
        except sqlite3.Error:
            self.rollback()
            return False

    def delete_role(self, name: str) -> bool:
        """Delete a role if it has no employees"""
        try:
            # Check if role has employees
            cursor = self.execute_query(
                """
                SELECT COUNT(*) as count
                FROM employees e
                JOIN roles r ON e.role_id = r.id
                WHERE r.name = ?
                """,
                (name,)
            )
            if cursor.fetchone()['count'] > 0:
                return False

            # Delete role if no employees
            self.execute_query(
                "DELETE FROM roles WHERE name = ?",
                (name,)
            )
            self.commit()
            return True
        except sqlite3.Error:
            self.rollback()
            return False

    def get_role(self, role_id: int) -> Optional[Dict]:
        """Get role information by ID."""
        self.cursor.execute(
            """
            SELECT 
                r.id,
                r.name,
                COUNT(e.id) as employee_count
            FROM roles r
            LEFT JOIN employees e ON r.id = e.role_id
            WHERE r.id = ?
            GROUP BY r.id, r.name
            """,
            (role_id,)
        )
        row = self.cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'employee_count': row[2]
            }
        return None

    def get_all_roles(self) -> List[Dict]:
        """Get all roles with employee count"""
        cursor = self.execute_query(
            """
            SELECT 
                r.id,
                r.code,
                r.name,
                COUNT(DISTINCT e.id) as employee_count
            FROM roles r
            LEFT JOIN employees e ON r.id = e.role_id
            GROUP BY r.id, r.code, r.name
            ORDER BY r.name
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_role_employees(self, role_id: int) -> List[Dict]:
        """جلب جميع الموظفين الذين لديهم دور معين"""
        cursor = self.execute_query(
            """
            SELECT 
                e.id,
                e.name,
                d.name as department_name
            FROM employees e
            JOIN departments d ON e.department_code = d.code
            WHERE e.role_id = ?
            ORDER BY e.name
            """,
            (role_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

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
            cursor = self.execute_query(
                "SELECT 1 FROM employees WHERE id = ?",
                (employee_id,)
            )
            if not cursor.fetchone():
                print(f"Employee {employee_id} not found")
                return False

            # التحقق من نوع الحالة وجلب تفاصيلها
            cursor = self.execute_query(
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
            self.execute_query(
                """
                INSERT INTO employee_status 
                (employee_id, status_type_id, start_date, end_date, notes, approved)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (employee_id, status_type_id, start_date, end_date, notes, approved)
            )

            self.commit()
            print(f"Successfully added status for employee {employee_id}")
            return True
        except sqlite3.Error as e:
            print(f"Error in add_employee_status: {str(e)}")
            self.rollback()
            return False

    def approve_employee_status(
            self,
            status_id: int,
            approved_by: str
    ) -> bool:
        """Approve an employee status record."""
        try:
            # Check if the approver is a manager
            self.cursor.execute(
                """
                SELECT 1 FROM employees e
                JOIN roles r ON e.role_id = r.id
                WHERE e.id = ? AND r.name = 'مدير'
                """,
                (approved_by,)
            )
            if not self.cursor.fetchone():
                return False  # Only managers can approve

            self.cursor.execute(
                """
                UPDATE employee_status 
                SET approved = TRUE, approved_by = ?
                WHERE id = ? AND approved = FALSE
                """,
                (approved_by, status_id)
            )
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error:
            return False

    def get_employee_status(
            self,
            employee_id: str,
            from_date: Optional[str] = None,
            to_date: Optional[str] = None
    ) -> List[Dict]:
        """Get status history for an employee."""
        query = """
                SELECT 
                    s.id,
                    t.name as status_type,
                    s.start_date,
                    s.end_date,
                    s.notes,
                    s.approved,
                    e.name as approved_by_name,
                    s.created_at
                FROM employee_status s
                JOIN status_types t ON s.status_type_id = t.id
                LEFT JOIN employees e ON s.approved_by = e.id
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

        cursor = self.execute_query(query, tuple(params))
        return [
            {
                'id': row[0],
                'status_type': row[1],
                'start_date': row[2],
                'end_date': row[3],
                'notes': row[4],
                'approved': bool(row[5]),
                'approved_by': row[6],
                'created_at': row[7]
            }
            for row in cursor.fetchall()
        ]

    def get_department_status(
            self,
            department_code: str,
            date: Optional[str] = None
    ) -> List[Dict]:
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
                    s.created_at
                FROM employees e
                JOIN employee_status s ON e.id = s.employee_id
                JOIN status_types t ON s.status_type_id = t.id
                WHERE e.department_code = ?
            """
        params = [department_code]
        if date:
            query += " AND s.start_date <= ? AND (s.end_date >= ? OR s.end_date IS NULL)"
            params.extend([date, date])
        cursor = self.execute_query(query, tuple(params))
        return [
            {
                'employee_id': row[0],
                'employee_name': row[1],
                'status_type': row[2],
                'start_date': row[3],
                'end_date': row[4],
                'notes': row[5],
                'approved': bool(row[6]),
                'approved_by': row[7],
                'created_at': row[8]
            }
            for row in cursor.fetchall()
        ]

    def get_status_id(self, employee_id: str, start_date: str) -> Optional[int]:
        """Get status ID for a specific employee and start date."""
        try:
            self.cursor.execute(
                """
                SELECT id
                FROM employee_status
                WHERE employee_id = ? AND start_date = ?
                """,
                (employee_id, start_date)
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except sqlite3.Error:
            return None

    def add_status_type(self, name: str, requires_approval: bool = True,
                        max_days: Optional[int] = None) -> bool:
        """إضافة نوع حالة جديد"""
        return self.execute_query_with_commit(
            """
            INSERT INTO status_types (name, requires_approval, max_days)
            VALUES (?, ?, ?)
            """,
            (name, requires_approval, max_days)
        )

    def update_status_type(self, current_name: str, new_name: str,
                           requires_approval: bool, max_days: Optional[int] = None) -> bool:
        """تحديث نوع حالة"""
        return self.execute_query_with_commit(
            """
            UPDATE status_types 
            SET name = ?, requires_approval = ?, max_days = ?
            WHERE name = ?
            """,
            (new_name, requires_approval, max_days, current_name)
        )

    def delete_status_type(self, name: str) -> bool:
        """حذف نوع حالة"""
        try:
            # التحقق من عدم وجود سجلات مرتبطة
            cursor = self.execute_query(
                """
                SELECT COUNT(*) as count
                FROM employee_status s
                JOIN status_types t ON s.status_type_id = t.id
                WHERE t.name = ?
                """,
                (name,)
            )
            if cursor.fetchone()['count'] > 0:
                return False

            return self.execute_query_with_commit(
                "DELETE FROM status_types WHERE name = ?",
                (name,)
            )
        except sqlite3.Error:
            return False

    def get_all_status_types(self) -> List[Dict]:
        """جلب جميع أنواع الحالات مع إحصائياتها"""
        cursor = self.execute_query(
            """
            SELECT 
                t.name,
                t.requires_approval,
                t.max_days,
                COUNT(s.id) as employee_count
            FROM status_types t
            LEFT JOIN employee_status s ON t.id = s.status_type_id
            GROUP BY t.id, t.name
            ORDER BY t.name
            """
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_shift_type(self, name: str, start_time: str, end_time: str,
                       break_duration: int = 60, flexible_minutes: int = 0,
                       overtime_allowed: bool = False) -> bool:
        """إضافة نوع وردية جديد"""
        return self.execute_query_with_commit(
            """
            INSERT INTO shift_types 
            (name, start_time, end_time, break_duration, flexible_minutes, overtime_allowed)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, start_time, end_time, break_duration, flexible_minutes, overtime_allowed)
        )

    def update_shift_type(self, current_name: str, new_name: str,
                          start_time: str, end_time: str, break_duration: int = 60,
                          flexible_minutes: int = 0, overtime_allowed: bool = False) -> bool:
        """تحديث نوع وردية"""
        return self.execute_query_with_commit(
            """
            UPDATE shift_types 
            SET name = ?, start_time = ?, end_time = ?, 
                break_duration = ?, flexible_minutes = ?, overtime_allowed = ?
            WHERE name = ?
            """,
            (new_name, start_time, end_time, break_duration,
             flexible_minutes, overtime_allowed, current_name)
        )

    def delete_shift_type(self, name: str) -> bool:
        """حذف نوع وردية"""
        try:
            # التحقق من عدم وجود سجلات مرتبطة
            cursor = self.execute_query(
                """
                SELECT COUNT(*) as count
                FROM employee_shifts s
                JOIN shift_types t ON s.shift_type_id = t.id
                WHERE t.name = ?
                """,
                (name,)
            )
            if cursor.fetchone()['count'] > 0:
                return False

            return self.execute_query_with_commit(
                "DELETE FROM shift_types WHERE name = ?",
                (name,)
            )
        except sqlite3.Error:
            return False

    def get_all_shift_types(self) -> List[Dict]:
        """جلب جميع أنواع الورديات مع إحصائياتها"""
        cursor = self.execute_query(
            """
            SELECT 
                t.id,
                t.name,
                t.start_time,
                t.end_time,
                t.break_duration,
                t.flexible_minutes,
                t.overtime_allowed,
                COUNT(s.id) as employee_count
            FROM shift_types t
            LEFT JOIN employee_shifts s ON t.id = s.shift_type_id
            GROUP BY t.id, t.name, t.start_time, t.end_time, 
                     t.break_duration, t.flexible_minutes, t.overtime_allowed
            ORDER BY t.name
            """
        )
        return [dict(row) for row in cursor.fetchall()]

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
            cursor = self.execute_query(
                "SELECT 1 FROM employees WHERE id = ?",
                (employee_id,)
            )
            if not cursor.fetchone():
                return False

            # التحقق من وجود الوردية
            cursor = self.execute_query(
                "SELECT 1 FROM shift_types WHERE id = ?",
                (shift_type_id,)
            )
            if not cursor.fetchone():
                return False

            # إضافة الوردية للموظف
            return self.execute_query_with_commit(
                """
                INSERT INTO employee_shifts 
                (employee_id, shift_type_id, start_date, end_date, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (employee_id, shift_type_id, start_date, end_date, notes)
            )
        except sqlite3.Error:
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

        cursor = self.execute_query(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def get_department_shifts(self, department_code: str, date: Optional[str] = None) -> List[Dict]:
        """جلب الورديات الحالية لجميع موظفي قسم معين"""
        query = """
                SELECT 
                    e.id as employee_id,
                    e.name as employee_name,
                    t.name as shift_name,
                    t.start_time,
                    t.end_time,
                    s.start_date,
                    s.end_date,
                    s.notes
                FROM employees e
                LEFT JOIN employee_shifts s ON e.id = s.employee_id
                LEFT JOIN shift_types t ON s.shift_type_id = t.id
                WHERE e.department_code = ?
            """
        params = [department_code]

        if date:
            query += " AND (s.start_date <= ? AND (s.end_date >= ? OR s.end_date IS NULL))"
            params.extend([date, date])

        query += " ORDER BY e.name"

        cursor = self.execute_query(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def get_all_attendance(self, date: str) -> List[Dict]:
        """جلب جميع سجلات الحضور في تاريخ محدد"""
        try:
            print(f"Getting attendance records for date: {date}")
            cursor = self.execute_query("""
                SELECT 
                    a.id,
                    a.employee_id,
                    e.name as employee_name,
                    d.name as department,
                    d.code as department_code,
                    st.name as shift_name,
                    a.check_in_time,
                    a.check_out_time,
                    a.source,
                    a.status,
                    CASE 
                        WHEN estat.id IS NOT NULL THEN stype.name
                        ELSE 'حاضر'
                    END as status_type
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                LEFT JOIN departments d ON e.department_code = d.code
                LEFT JOIN employee_shifts esh ON e.id = esh.employee_id 
                    AND ? BETWEEN esh.start_date AND COALESCE(esh.end_date, ?)
                LEFT JOIN shift_types st ON esh.shift_type_id = st.id
                LEFT JOIN employee_status estat ON e.id = estat.employee_id 
                    AND ? BETWEEN estat.start_date AND COALESCE(estat.end_date, ?)
                LEFT JOIN status_types stype ON estat.status_type_id = stype.id
                WHERE a.date = ?
                ORDER BY a.check_in_time DESC
                """, (date, date, date, date, date))

            records = []
            for row in cursor.fetchall():
                record = {
                    'id': row['id'],
                    'employee_id': row['employee_id'],
                    'name': row['employee_name'],
                    'department': row['department'],
                    'department_code': row['department_code'],
                    'shift_name': row['shift_name'],
                    'check_in_time': row['check_in_time'],
                    'check_out_time': row['check_out_time'],
                    'source': row['source'],
                    'status': row['status'],
                    'status_type': row['status_type']
                }
                records.append(record)

            print(f"Found {len(records)} attendance records")
            return records

        except sqlite3.Error as e:
            print(f"Error getting attendance records: {e}")
            return []

    def get_department_attendance(self, dept_code: str, date_str: str) -> List[Dict]:
        """جلب سجلات حضور قسم معين في تاريخ محدد"""
        try:
            print(f"Getting attendance records for department {dept_code} on {date_str}")
            cursor = self.execute_query("""
                SELECT 
                    a.id,
                    a.employee_id,
                    e.name as employee_name,
                    d.name as department,
                    d.code as department_code,
                    st.name as shift_name,
                    a.check_in_time,
                    a.check_out_time,
                    a.source,
                    a.status,
                    CASE 
                        WHEN estat.id IS NOT NULL THEN stype.name
                        ELSE 'حاضر'
                    END as status_type
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                LEFT JOIN departments d ON e.department_code = d.code
                LEFT JOIN employee_shifts esh ON e.id = esh.employee_id 
                    AND ? BETWEEN esh.start_date AND COALESCE(esh.end_date, ?)
                LEFT JOIN shift_types st ON esh.shift_type_id = st.id
                LEFT JOIN employee_status estat ON e.id = estat.employee_id 
                    AND ? BETWEEN estat.start_date AND COALESCE(estat.end_date, ?)
                LEFT JOIN status_types stype ON estat.status_type_id = stype.id
                WHERE d.code = ? AND a.date = ?
                ORDER BY a.check_in_time DESC
                """, (date_str, date_str, date_str, date_str, dept_code, date_str))

            records = []
            for row in cursor.fetchall():
                record = {
                    'id': row['id'],
                    'employee_id': row['employee_id'],
                    'name': row['employee_name'],
                    'department': row['department'],
                    'department_code': row['department_code'],
                    'shift_name': row['shift_name'],
                    'check_in_time': row['check_in_time'],
                    'check_out_time': row['check_out_time'],
                    'source': row['source'],
                    'status': row['status'],
                    'status_type': row['status_type']
                }
                records.append(record)

            print(f"Found {len(records)} attendance records for department {dept_code}")
            return records

        except sqlite3.Error as e:
            print(f"Error getting department attendance records: {e}")
            return []

    def get_today_attendance(self) -> List[Dict]:
        """جلب سجلات حضور اليوم"""
        current_date = date.today().isoformat()
        print(f"Getting attendance for date: {current_date}")

        cursor = self.execute_query("""
                SELECT a.*, e.name,
                       d.name as department_name,
                       st.name as shift_name
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                LEFT JOIN departments d ON e.department_code = d.code
                LEFT JOIN employee_shifts es ON e.id = es.employee_id 
                    AND ? BETWEEN es.start_date AND COALESCE(es.end_date, ?)
                LEFT JOIN shift_types st ON es.shift_type_id = st.id
                WHERE a.date = ?
                ORDER BY a.check_in_time DESC
            """, (current_date, current_date, current_date))

        records = [dict(row) for row in cursor.fetchall()]
        print(f"Found {len(records)} records")
        return records

    def get_all_status(self, from_date: str = None, to_date: str = None, approved: bool = None) -> List[Dict]:
        """جلب جميع سجلات الحالات مع التصفية الاختيارية"""
        query = """
                SELECT 
                    s.id,
                    e.id as employee_id,
                    e.name as employee_name,
                    d.name as department,
                    t.name as status_type,
                    s.start_date,
                    s.end_date,
                    s.notes,
                    s.approved,
                    m.name as approved_by_name
                FROM employee_status s
                JOIN employees e ON s.employee_id = e.id
                JOIN departments d ON e.department_code = d.code
                JOIN status_types t ON s.status_type_id = t.id
                LEFT JOIN employees m ON s.approved_by = m.id
                WHERE 1=1
            """
        params = []

        if from_date:
            query += " AND (s.end_date >= ? OR s.end_date IS NULL)"
            params.append(from_date)

        if to_date:
            query += " AND s.start_date <= ?"
            params.append(to_date)

        if approved is not None:
            query += " AND s.approved = ?"
            params.append(approved)

        query += " ORDER BY s.start_date DESC"

        cursor = self.execute_query(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def get_all_permissions(self) -> List[Dict]:
        """جلب جميع الصلاحيات المتاحة"""
        cursor = self.execute_query("""
                SELECT id, code, name, description
                FROM permissions
                ORDER BY name
            """)
        return [dict(row) for row in cursor.fetchall()]

    def get_role_permissions(self, role_id: int) -> List[Dict]:
        """Get permissions for a role"""
        cursor = self.execute_query(
            """
            SELECT 
                p.code,
                p.name,
                p.description,
                CASE WHEN rp.role_id IS NOT NULL THEN 1 ELSE 0 END as granted
            FROM permissions p
            LEFT JOIN role_permissions rp ON p.code = rp.permission_code AND rp.role_id = ?
            ORDER BY p.name
            """,
            (role_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_user_permissions(self, role_id: int) -> List[str]:
        """Get list of permission codes for a role"""
        try:
            print(f"Getting permissions for role {role_id}")
            cursor = self.execute_query(
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

    def get_all_overtime(self, from_date: str, to_date: str) -> List[Dict]:
        """جلب ملخص الوقت الإضافي لجميع الموظفين في فترة زمنية"""
        cursor = self.execute_query(
            """
            WITH overtime_hours AS (
                SELECT 
                    a.employee_id,
                    a.date,
                    t.name as shift_name,
                    CASE
                        WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL THEN
                            CAST(
                                (
                                    strftime('%s', a.check_out_time) - 
                                    strftime('%s', a.check_in_time)
                                ) / 3600.0 as REAL
                            ) -
                            CAST(
                                (
                                    strftime('%s', t.end_time) - 
                                    strftime('%s', t.start_time)
                                ) / 3600.0 as REAL
                            )
                        ELSE 0
                    END as overtime_hours
                FROM attendance a
                LEFT JOIN employee_shifts es ON a.employee_id = es.employee_id 
                    AND a.date BETWEEN es.start_date AND COALESCE(es.end_date, a.date)
                LEFT JOIN shift_types t ON es.shift_type_id = t.id
                WHERE 
                    t.overtime_allowed = TRUE
                    AND a.date BETWEEN ? AND ?
                    AND a.check_in_time IS NOT NULL 
                    AND a.check_out_time IS NOT NULL
            )
            SELECT 
                e.id,
                e.name,
                d.name as department,
                MAX(oh.shift_name) as shift_name,
                COUNT(DISTINCT oh.date) as days_count,
                SUM(oh.overtime_hours) as total_hours,
                AVG(oh.overtime_hours) as average_hours
            FROM employees e
            JOIN departments d ON e.department_code = d.code
            LEFT JOIN overtime_hours oh ON e.id = oh.employee_id
            GROUP BY e.id, e.name, d.name
            HAVING total_hours > 0
            ORDER BY total_hours DESC
            """,
            (from_date, to_date)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_department_overtime(self, department_code: str, from_date: str, to_date: str) -> List[Dict]:
        """جلب ملخص الوقت الإضافي لموظفي قسم معين في فترة زمنية"""
        cursor = self.execute_query(
            """
            WITH overtime_hours AS (
                SELECT 
                    a.employee_id,
                    a.date,
                    t.name as shift_name,
                    CASE
                        WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL THEN
                            CAST(
                                (
                                    strftime('%s', a.check_out_time) - 
                                    strftime('%s', a.check_in_time)
                                ) / 3600.0 as REAL
                            ) -
                            CAST(
                                (
                                    strftime('%s', t.end_time) - 
                                    strftime('%s', t.start_time)
                                ) / 3600.0 as REAL
                            )
                        ELSE 0
                    END as overtime_hours
                FROM attendance a
                LEFT JOIN employee_shifts es ON a.employee_id = es.employee_id 
                    AND a.date BETWEEN es.start_date AND COALESCE(es.end_date, a.date)
                LEFT JOIN shift_types t ON es.shift_type_id = t.id
                WHERE 
                    t.overtime_allowed = TRUE
                    AND a.date BETWEEN ? AND ?
                    AND a.check_in_time IS NOT NULL 
                    AND a.check_out_time IS NOT NULL
            )
            SELECT 
                e.id,
                e.name,
                d.name as department,
                MAX(oh.shift_name) as shift_name,
                COUNT(DISTINCT oh.date) as days_count,
                SUM(oh.overtime_hours) as total_hours,
                AVG(oh.overtime_hours) as average_hours
            FROM employees e
            JOIN departments d ON e.department_code = d.code
            LEFT JOIN overtime_hours oh ON e.id = oh.employee_id
            WHERE e.department_code = ?
            GROUP BY e.id, e.name, d.name
            HAVING total_hours > 0
            ORDER BY total_hours DESC
            """,
            (from_date, to_date, department_code)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_current_user(self) -> Optional[Dict]:
        """جلب معلومات المستخدم الحالي"""
        try:
            cursor = self.execute_query("""
                    SELECT 
                        e.id,
                        e.name,
                        e.department_code,
                        r.name as role_name,
                        r.id as role_id
                    FROM current_session cs
                    JOIN employees e ON cs.employee_id = e.id
                    JOIN roles r ON e.role_id = r.id
                    WHERE cs.logged_out_at IS NULL
                    ORDER BY cs.logged_in_at DESC
                    LIMIT 1
                """)

            result = cursor.fetchone()
            if result:
                return dict(result)
            return None

        except Exception as e:
            print(f"Error getting current user: {str(e)}")
            return None

    def login_user(self, employee_id: str, password: str) -> Optional[Dict]:
        """تسجيل دخول المستخدم"""
        try:
            # التحقق من صحة بيانات الدخول
            cursor = self.execute_query("""
                    SELECT 
                        e.id,
                        e.name,
                        e.department_code,
                        r.name as role_name,
                        r.id as role_id
                    FROM employees e
                    JOIN roles r ON e.role_id = r.id
                    WHERE e.id = ? AND e.password = ?
                """, (employee_id, password))

            user = cursor.fetchone()
            if not user:
                return None

            # تسجيل الجلسة الجديدة
            self.execute_query("""
                    INSERT INTO current_session (employee_id)
                    VALUES (?)
                """, (employee_id,))

            self.commit()
            return dict(user)

        except Exception as e:
            print(f"Error in login: {str(e)}")
            self.rollback()
            return None

    def logout_user(self, employee_id: str) -> bool:
        """تسجيل خروج المستخدم"""
        try:
            self.execute_query("""
                    UPDATE current_session
                    SET logged_out_at = CURRENT_TIMESTAMP
                    WHERE employee_id = ? 
                    AND logged_out_at IS NULL
                """, (employee_id,))

            self.commit()
            return True

        except Exception as e:
            print(f"Error in logout: {str(e)}")
            self.rollback()
            return False

    def update_database_schema(self):
        """تحديث هيكل قاعدة البيانات"""
        try:
            # تحديث الأعمدة المفقودة في جداول قاعدة البيانات
            self.conn.executescript("""
                    -- تحديث جدول attendance
                    ALTER TABLE attendance ADD COLUMN source TEXT DEFAULT 'manual';
                    ALTER TABLE attendance ADD COLUMN device_id TEXT;
                    ALTER TABLE attendance ADD COLUMN status TEXT DEFAULT 'present';

                    -- تحديث جدول departments لإضافة عمود manager_id
                    ALTER TABLE departments ADD COLUMN manager_id TEXT;
                """)

            self.conn.commit()
            print("Database schema updated successfully")

        except sqlite3.Error as e:
            if 'duplicate column name' not in str(e).lower():
                print(f"Error updating database schema: {e}")
                self.conn.rollback()
            else:
                print("Columns already exist")

    def set_role_permissions(self, role_id: int, permission_codes: List[str]) -> bool:
        """Set permissions for a role"""
        try:
            # Delete existing permissions
            self.execute_query(
                "DELETE FROM role_permissions WHERE role_id = ?",
                (role_id,)
            )

            # Add new permissions
            for code in permission_codes:
                self.execute_query(
                    """
                    INSERT INTO role_permissions (role_id, permission_code)
                    VALUES (?, ?)
                    """,
                    (role_id, code)
                )

            self.commit()
            return True
        except sqlite3.Error:
            self.rollback()
            return False

    def create_session(self, employee_id: str, role_id: int, hours: int = 12) -> Optional[str]:
        """Create a new session for the user"""
        try:
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=hours)

            self.execute_query(
                """
                INSERT INTO sessions 
                (id, employee_id, role_id, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, employee_id, role_id, expires_at.isoformat())
            )
            self.commit()
            return session_id
        except sqlite3.Error:
            self.rollback()
            return None

    def verify_session(self, session_id: str) -> Optional[tuple]:
        """Verify session and return (employee_id, role_code) if valid"""
        try:
            cursor = self.execute_query(
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
                self.execute_query(
                    """
                    UPDATE sessions
                    SET last_activity = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (session_id,)
                )
                self.commit()

                print(f"تم التحقق من توكن تذكرني للموظف {result['employee_id']}")
                return (result['employee_id'], result['role_code'])

            print("توكن تذكرني غير صالح أو منتهي الصلاحية")
            return None

        except sqlite3.Error as e:
            print(f"خطأ في التحقق من توكن تذكرني: {str(e)}")
            return None

    def end_session(self, session_id: str) -> bool:
        """End a session"""
        try:
            self.execute_query(
                """
                DELETE FROM sessions
                WHERE id = ?
                """,
                (session_id,)
            )
            self.commit()
            return True
        except sqlite3.Error:
            self.rollback()
            return False

    def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
        try:
            self.execute_query(
                """
                DELETE FROM sessions
                WHERE expires_at <= datetime('now')
                """
            )
            self.commit()
        except sqlite3.Error:
            self.rollback()

    def initialize_default_departments(self):
        """Insert default departments if none exist."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM departments")
            count = cursor.fetchone()[0]
            if count == 0:
                default_departments = [
                    {"code": "ADM", "name": "الإدارة"},
                    {"code": "SAL", "name": "المبيعات"},
                    {"code": "ACC", "name": "المحاسبة"},
                    {"code": "MKT", "name": "التسويق"},
                    {"code": "IT", "name": "الدعم الفني"}
                ]
                for dept in default_departments:
                    cursor.execute("INSERT INTO departments (code, name) VALUES (?, ?)", (dept["code"], dept["name"]))
                self.conn.commit()
        except Exception as e:
            print("Error initializing default departments:", e)

    def add_attendance(self, employee_id: str, date: str, action: str, source: str = 'manual',
                       device_id: Optional[str] = None) -> bool:
        """إضافة سجل حضور أو انصراف جديد"""
        try:
            print(f"Adding {action} record for employee {employee_id} on {date}")

            # التحقق من وجود الموظف
            cursor = self.execute_query(
                "SELECT 1 FROM employees WHERE id = ?",
                (employee_id,)
            )
            if not cursor.fetchone():
                print(f"Employee {employee_id} not found")
                return False

            # تحويل التاريخ إلى التنسيق المطلوب
            try:
                current_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                db_date = current_date.strftime("%Y-%m-%d")
                current_time = current_date.strftime("%H:%M:%S")
            except ValueError as e:
                print(f"Invalid date format: {e}")
                return False

            # جلب سجل الحضور الحالي لليوم
            cursor = self.execute_query(
                "SELECT * FROM attendance WHERE employee_id = ? AND date = ?",
                (employee_id, db_date)
            )
            current_record = cursor.fetchone()

            if action == 'check_in':
                if current_record:
                    if current_record['check_in_time']:
                        print("Check-in record already exists")
                        return False
                    # تحديث وقت الحضور
                    self.execute_query(
                        """
                        UPDATE attendance 
                        SET check_in_time = ?,
                            source = ?,
                            device_id = ?,
                            status = 'present'
                        WHERE employee_id = ? AND date = ?
                        """,
                        (current_time, source, device_id, employee_id, db_date)
                    )
                else:
                    # إنشاء سجل جديد
                    self.execute_query(
                        """
                        INSERT INTO attendance 
                        (employee_id, date, check_in_time, source, device_id, status)
                        VALUES (?, ?, ?, ?, ?, 'present')
                        """,
                        (employee_id, db_date, current_time, source, device_id)
                    )
            elif action == 'check_out':
                if not current_record:
                    print("No check-in record found")
                    return False
                if current_record['check_out_time']:
                    print("Check-out record already exists")
                    return False
                # تحديث وقت الانصراف
                self.execute_query(
                    """
                    UPDATE attendance 
                    SET check_out_time = ?,
                        source = ?,
                        device_id = ?
                    WHERE employee_id = ? AND date = ?
                    """,
                    (current_time, source, device_id, employee_id, db_date)
                )
            else:
                print(f"Invalid action: {action}")
                return False

            self.commit()
            print(f"Successfully added {action} record")
            return True

        except Exception as e:
            print(f"Error adding attendance record: {str(e)}")
            self.rollback()
            return False

    def initialize_default_shifts(self):
        """إضافة أنواع الورديات الافتراضية إذا لم تكن موجودة"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shift_types")
            count = cursor.fetchone()[0]
            if count == 0:
                default_shifts = [
                    {
                        "name": "الوردية الصباحية",
                        "start_time": "08:00:00",
                        "end_time": "16:00:00",
                        "break_duration": 60,
                        "flexible_minutes": 30,
                        "overtime_allowed": True
                    },
                    {
                        "name": "الوردية المسائية",
                        "start_time": "16:00:00",
                        "end_time": "00:00:00",
                        "break_duration": 60,
                        "flexible_minutes": 30,
                        "overtime_allowed": True
                    },
                    {
                        "name": "الوردية الليلية",
                        "start_time": "00:00:00",
                        "end_time": "08:00:00",
                        "break_duration": 60,
                        "flexible_minutes": 30,
                        "overtime_allowed": True
                    },
                    {
                        "name": "دوام مرن",
                        "start_time": "07:00:00",
                        "end_time": "19:00:00",
                        "break_duration": 60,
                        "flexible_minutes": 120,
                        "overtime_allowed": False
                    }
                ]

                for shift in default_shifts:
                    cursor.execute(
                        """
                        INSERT INTO shift_types 
                        (name, start_time, end_time, break_duration, flexible_minutes, overtime_allowed)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            shift["name"],
                            shift["start_time"],
                            shift["end_time"],
                            shift["break_duration"],
                            shift["flexible_minutes"],
                            shift["overtime_allowed"]
                        )
                    )
                self.conn.commit()
                print("تم إضافة الورديات الافتراضية بنجاح")
        except Exception as e:
            print(f"خطأ في إضافة الورديات الافتراضية: {str(e)}")
            self.conn.rollback()

    def create_remember_me_token(self, employee_id: str, device_info: str = None, ip_address: str = None, days: int = 30) -> \
    Optional[str]:
        """إنشاء توكن تذكرني جديد"""
        try:
            # إنشاء توكن عشوائي
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(days=days)

            # حذف التوكنات القديمة للموظف على نفس الجهاز
            if device_info:
                self.execute_query(
                    """
                    DELETE FROM remember_me_tokens
                    WHERE employee_id = ? AND device_info = ?
                    """,
                    (employee_id, device_info)
                )

            # إضافة التوكن الجديد
            self.execute_query(
                """
                INSERT INTO remember_me_tokens 
                (token, employee_id, device_info, ip_address, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (token, employee_id, device_info, ip_address, expires_at.isoformat())
            )

            self.commit()
            print(f"تم إنشاء توكن تذكرني جديد للموظف {employee_id}")
            return token

        except sqlite3.Error as e:
            print(f"خطأ في إنشاء توكن تذكرني: {str(e)}")
            self.rollback()
            return None

    def verify_remember_me_token(self, token: str, device_info: str = None) -> Optional[tuple]:
        """التحقق من صحة توكن تذكرني وإرجاع معلومات الموظف إذا كان صالحاً"""
        try:
            # التحقق من التوكن وجلب معلومات الموظف
            cursor = self.execute_query(
                """
                SELECT 
                    t.employee_id,
                    t.device_info,
                    e.role_id,
                    r.code as role_code
                FROM remember_me_tokens t
                JOIN employees e ON t.employee_id = e.id
                JOIN roles r ON e.role_id = r.id
                WHERE t.token = ?
                AND t.expires_at > datetime('now')
                AND (t.device_info IS NULL OR t.device_info = ?)
                """,
                (token, device_info)
            )
            result = cursor.fetchone()

            if result:
                # تحديث وقت آخر استخدام
                self.execute_query(
                    """
                    UPDATE remember_me_tokens
                    SET last_used_at = CURRENT_TIMESTAMP
                    WHERE token = ?
                    """,
                    (token,)
                )
                self.commit()

                print(f"تم التحقق من توكن تذكرني للموظف {result['employee_id']}")
                return (result['employee_id'], result['role_code'], result['role_id'])

            print("توكن تذكرني غير صالح أو منتهي الصلاحية")
            return None

        except sqlite3.Error as e:
            print(f"خطأ في التحقق من توكن تذكرني: {str(e)}")
            return None

    def clear_remember_me_tokens(self, employee_id: str = None, device_info: str = None) -> bool:
        """حذف توكنات تذكرني"""
        try:
            query = "DELETE FROM remember_me_tokens WHERE 1=1"
            params = []

            if employee_id:
                query += " AND employee_id = ?"
                params.append(employee_id)

            if device_info:
                query += " AND device_info = ?"
                params.append(device_info)

            self.execute_query(query, tuple(params))
            self.commit()

            print("تم حذف توكنات تذكرني بنجاح")
            return True

        except sqlite3.Error as e:
            print(f"خطأ في حذف توكنات تذكرني: {str(e)}")
            self.rollback()
            return False

    def cleanup_expired_tokens(self) -> None:
        """تنظيف التوكنات منتهية الصلاحية"""
        try:
            self.execute_query(
                """
                DELETE FROM remember_me_tokens
                WHERE expires_at <= datetime('now')
                """
            )
            self.commit()
        except sqlite3.Error as e:
            print(f"خطأ في تنظيف التوكنات: {str(e)}")
            self.rollback()

    def initialize_default_roles(self):
        """إضافة الأدوار الأساسية إذا لم تكن موجودة"""
        try:
            default_roles = [
                ("مدير", "admin"),
                ("موظف", "employee"),
                ("مشرف", "supervisor")
            ]
            
            cursor = self.conn.cursor()
            for role_name, role_code in default_roles:
                cursor.execute(
                    "INSERT OR IGNORE INTO roles (name, code) VALUES (?, ?)",
                    (role_name, role_code)
                )
            self.conn.commit()
            print("تم إضافة الأدوار الافتراضية بنجاح")
        except Exception as e:
            print(f"خطأ في إضافة الأدوار الافتراضية: {str(e)}")
            self.conn.rollback()

    def initialize_default_users(self):
        """إنشاء مستخدم مدير افتراضي إذا لم يوجد أي مديرين"""
        try:
            cursor = self.conn.cursor()
            
            # التحقق من وجود أي مديرين
            cursor.execute("""
                SELECT COUNT(*) 
                FROM employees e
                JOIN roles r ON e.role_id = r.id
                WHERE r.code = 'admin'
            """)
            admin_count = cursor.fetchone()[0]
            
            if admin_count == 0:
                # إنشاء مستخدم مدير افتراضي
                default_password = "admin123"  # كلمة مرور افتراضية
                hashed_password = "هنا يتم استخدام دالة التجزئة المناسبة"
                
                # الحصول على معرف دور المدير
                cursor.execute("SELECT id FROM roles WHERE code = 'admin'")
                role_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO employees (
                        id, 
                        name, 
                        password_hash, 
                        role_id,
                        department_code
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    "ADM001",
                    "المدير الافتراضي",
                    hashed_password,
                    role_id,
                    "ADM"
                ))
                
                self.conn.commit()
                print("تم إنشاء المدير الافتراضي بنجاح")
        except Exception as e:
            print(f"خطأ في إنشاء المدير الافتراضي: {str(e)}")
            self.conn.rollback()
