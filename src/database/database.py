import sqlite3
from pathlib import Path
from typing import Optional

class Database:
    def __init__(self, db_path: str):
        """Initialize database connection"""
        self.db_path = db_path
        self._connection = None
        self.connect()
        
    def connect(self):
        """Create a database connection."""
        try:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            
    def commit(self):
        """Commit changes to the database."""
        if self._connection:
            self._connection.commit()
            
    def rollback(self):
        """Rollback changes."""
        if self._connection:
            self._connection.rollback()
            
    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return the cursor."""
        conn = self.get_connection()
        if params:
            return conn.execute(query, params)
        return conn.execute(query)
        
    def execute_query_with_commit(self, query: str, params: tuple = None):
        """Execute a query and commit changes."""
        try:
            cursor = self.execute_query(query, params)
            self.commit()
            return cursor
        except sqlite3.Error:
            self.rollback()
            raise
            
    def get_connection(self):
        """Get the database connection."""
        if not self._connection:
            self.connect()
        return self._connection
        
    def create_tables(self):
        """Create all required tables."""
        try:
            # Start transaction
            self._connection.execute("BEGIN TRANSACTION")
            
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
            
            # Create current session table
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS current_session (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    logged_in_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    logged_out_at TIMESTAMP DEFAULT NULL,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
                )
            """)
            
            # Create roles table
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create permissions table
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create role permissions table
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id INTEGER NOT NULL,
                    permission_code TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (role_id, permission_code),
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
                    FOREIGN KEY (permission_code) REFERENCES permissions(code) ON DELETE CASCADE
                )
            """)
            
            # Create user permissions table
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS user_permissions (
                    employee_id TEXT NOT NULL,
                    permission_code TEXT NOT NULL,
                    granted_by TEXT NOT NULL,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (employee_id, permission_code),
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                    FOREIGN KEY (permission_code) REFERENCES permissions(code) ON DELETE CASCADE,
                    FOREIGN KEY (granted_by) REFERENCES employees(id) ON DELETE CASCADE
                )
            """)
            
            # Insert default roles if they don't exist
            default_roles = [
                ('ADMIN', 'مدير النظام'),
                ('HR', 'مسؤول الموارد البشرية'),
                ('EMPLOYEE', 'موظف')
            ]
            for role_code, role_name in default_roles:
                self._connection.execute(
                    """
                    INSERT OR IGNORE INTO roles (code, name)
                    VALUES (?, ?)
                    """,
                    (role_code, role_name)
                )
                
            # Insert default permissions
            default_permissions = [
                ('MANAGE_USERS', 'إدارة المستخدمين', 'إضافة وتعديل وحذف بيانات المستخدمين'),
                ('MANAGE_DEPARTMENTS', 'إدارة الأقسام', 'إضافة وتعديل وحذف الأقسام'),
                ('MANAGE_ATTENDANCE', 'إدارة الحضور والانصراف', 'تسجيل وتعديل بيانات الحضور والانصراف'),
                ('MANAGE_HR', 'إدارة الموارد البشرية', 'إدارة الإجازات والورديات والحالات'),
                ('MANAGE_ROLES', 'إدارة الأدوار', 'إدارة الأدوار والصلاحيات'),
                ('VIEW_REPORTS', 'عرض التقارير', 'الوصول إلى تقارير النظام'),
                ('VIEW_OWN_DATA', 'عرض البيانات الشخصية', 'عرض البيانات الشخصية للموظف')
            ]
            
            for perm in default_permissions:
                self._connection.execute(
                    """
                    INSERT OR IGNORE INTO permissions (code, name, description)
                    VALUES (?, ?, ?)
                    """,
                    perm
                )
            
            # Grant all permissions to admin role
            self._connection.execute(
                """
                INSERT OR IGNORE INTO role_permissions (role_id, permission_code)
                SELECT r.id, p.code
                FROM roles r, permissions p
                WHERE r.code = 'ADMIN'
                """
            )
            
            # Grant HR permissions to HR role
            hr_permissions = ['MANAGE_USERS', 'MANAGE_HR', 'VIEW_REPORTS']
            for perm in hr_permissions:
                self._connection.execute(
                    """
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_code)
                    SELECT r.id, ?
                    FROM roles r
                    WHERE r.code = 'HR'
                    """,
                    (perm,)
                )
            
            # Grant basic permissions to employee role
            employee_permissions = ['VIEW_OWN_DATA']
            for perm in employee_permissions:
                self._connection.execute(
                    """
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_code)
                    SELECT r.id, ?
                    FROM roles r
                    WHERE r.code = 'EMPLOYEE'
                    """,
                    (perm,)
                )
            
            # 2. Status types table
            self._connection.execute('''
                CREATE TABLE IF NOT EXISTS status_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    requires_approval BOOLEAN DEFAULT TRUE,
                    max_days INTEGER DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default status types
            default_statuses = [
                ('إجازة سنوية', True, 21),
                ('إجازة مرضية', True, 30),
                ('مأمورية', True, None),
                ('انتداب', True, None),
                ('عمل عن بعد', True, None),
                ('حضور', False, None)
            ]
            for status in default_statuses:
                self._connection.execute(
                    "INSERT OR IGNORE INTO status_types (name, requires_approval, max_days) VALUES (?, ?, ?)",
                    status
                )
            
            # 3. Shift types table
            self._connection.execute('''
                CREATE TABLE IF NOT EXISTS shift_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    break_duration INTEGER DEFAULT 60,  -- Break duration in minutes
                    flexible_minutes INTEGER DEFAULT 0,  -- Allowed flexibility in minutes
                    overtime_allowed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default shift types
            default_shifts = [
                ('صباحي', '08:00', '16:00', 60, 15, True),
                ('مسائي', '16:00', '00:00', 60, 15, True),
                ('ليلي', '00:00', '08:00', 60, 15, True)
            ]
            for shift in default_shifts:
                self._connection.execute(
                    """
                    INSERT OR IGNORE INTO shift_types 
                    (name, start_time, end_time, break_duration, flexible_minutes, overtime_allowed) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    shift
                )
            
            # 4. Employee shifts table
            self._connection.execute('''
                CREATE TABLE IF NOT EXISTS employee_shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    shift_type_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    FOREIGN KEY (shift_type_id) REFERENCES shift_types (id)
                )
            ''')
            
            # Create indices for better performance
            self._connection.execute('CREATE INDEX IF NOT EXISTS idx_emp_shifts ON employee_shifts(employee_id)')
            self._connection.execute('CREATE INDEX IF NOT EXISTS idx_shift_dates ON employee_shifts(start_date, end_date)')
            
            # 3. Departments table (no foreign key dependencies)
            self._connection.execute('''
                CREATE TABLE IF NOT EXISTS departments (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    manager_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 4. Employees table (depends on departments and roles)
            self._connection.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department_code TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (department_code) REFERENCES departments (code),
                    FOREIGN KEY (role_id) REFERENCES roles (id)
                )
            ''')
            
            # 5. Employee status table
            self._connection.execute('''
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
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    FOREIGN KEY (status_type_id) REFERENCES status_types (id),
                    FOREIGN KEY (approved_by) REFERENCES employees (id)
                )
            ''')
            
            # 6. Create trigger for manager role check if it doesn't exist
            self._connection.execute('''
                CREATE TRIGGER IF NOT EXISTS check_manager_role
                BEFORE UPDATE OF manager_id ON departments
                WHEN NEW.manager_id IS NOT NULL
                BEGIN
                    SELECT CASE 
                        WHEN NOT EXISTS (
                            SELECT 1 FROM employees e 
                            JOIN roles r ON e.role_id = r.id 
                            WHERE e.id = NEW.manager_id AND r.name = 'مدير'
                        )
                        THEN RAISE(ABORT, 'Manager must have manager role')
                    END;
                END;
            ''')
            
            # 7. Department history table
            self._connection.execute('''
                CREATE TABLE IF NOT EXISTS department_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    old_department_code TEXT NOT NULL,
                    new_department_code TEXT NOT NULL,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    FOREIGN KEY (old_department_code) REFERENCES departments (code),
                    FOREIGN KEY (new_department_code) REFERENCES departments (code)
                )
            ''')
            
            # 8. Attendance table
            self._connection.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    check_in_time TIME,
                    check_out_time TIME,
                    shift_type_id INTEGER,
                    FOREIGN KEY (employee_id) REFERENCES employees (id),
                    FOREIGN KEY (shift_type_id) REFERENCES shift_types (id)
                )
            ''')
            
            # Create sessions table
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                )
            """)
            
            # Create index on sessions expiry
            self._connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_expiry 
                ON sessions(expires_at)
            """)
            
            # Create index on sessions last activity
            self._connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_activity 
                ON sessions(last_activity)
            """)
            
            # Create indices for better performance if they don't exist
            self._connection.execute('CREATE INDEX IF NOT EXISTS idx_emp_dept ON employees(department_code)')
            self._connection.execute('CREATE INDEX IF NOT EXISTS idx_emp_role ON employees(role_id)')
            self._connection.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
            self._connection.execute('CREATE INDEX IF NOT EXISTS idx_attendance_employee ON attendance(employee_id)')
            self._connection.execute('CREATE INDEX IF NOT EXISTS idx_status_employee ON employee_status(employee_id)')
            self._connection.execute('CREATE INDEX IF NOT EXISTS idx_status_date ON employee_status(start_date, end_date)')
            
            self._connection.commit()
            
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            self._connection.rollback()
            
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with transaction support"""
        if not self._connection:
            print("Creating new connection")
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            # Set isolation level to IMMEDIATE to start transaction
            self._connection.isolation_level = "IMMEDIATE"
            print(f"Transaction started: {self._connection.in_transaction}")
        return self._connection
        
    def commit(self):
        """Commit changes."""
        if self._connection:
            self._connection.commit()
            
    def rollback(self):
        """Rollback changes."""
        if self._connection:
            self._connection.rollback()
            
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query and return the cursor."""
        return self._connection.execute(query, params)
        
    def execute_query_with_commit(self, query: str, params: tuple = ()) -> bool:
        """Execute a query and commit the changes."""
        try:
            self._connection.execute(query, params)
            self.commit()
            return True
        except sqlite3.Error:
            self.rollback()
            return False 