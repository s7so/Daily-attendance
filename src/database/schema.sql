-- Create tables in correct order (handling dependencies)

-- 1. Basic tables without foreign keys
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE IF NOT EXISTS status_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    requires_approval BOOLEAN DEFAULT TRUE,
    max_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fingerprint_devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    model TEXT,
    ip_address TEXT,
    port INTEGER,
    location TEXT,
    status TEXT DEFAULT 'active',
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    manager_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tables with foreign keys to basic tables
CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department_code TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    shift_type_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_code) REFERENCES departments(code),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id)
);

-- Add foreign key for manager_id after employees table is created
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

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- 3. Tables with foreign keys to employees and basic tables
CREATE TABLE IF NOT EXISTS department_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    old_department_code TEXT NOT NULL,
    new_department_code TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (old_department_code) REFERENCES departments(code),
    FOREIGN KEY (new_department_code) REFERENCES departments(code)
);

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

CREATE TABLE IF NOT EXISTS attendance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    date DATE NOT NULL,
    check_in TIME,
    check_out TIME,
    status TEXT DEFAULT 'present',
    source TEXT DEFAULT 'manual',
    device_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (device_id) REFERENCES fingerprint_devices(id)
);

CREATE TABLE IF NOT EXISTS user_permissions (
    employee_id TEXT NOT NULL,
    permission_id INTEGER NOT NULL,
    granted_by TEXT NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (employee_id, permission_id),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES employees(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS device_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES fingerprint_devices(id)
);

CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES fingerprint_devices(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS employee_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    photo_data BLOB NOT NULL,
    source TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Create indices for better performance
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department_code);
CREATE INDEX IF NOT EXISTS idx_employees_role ON employees(role_id);
CREATE INDEX IF NOT EXISTS idx_employees_shift ON employees(shift_type_id);
CREATE INDEX IF NOT EXISTS idx_department_history_employee ON department_history(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_status_employee ON employee_status(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_shifts_employee ON employee_shifts(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_shifts_shift ON employee_shifts(shift_type_id);
CREATE INDEX IF NOT EXISTS idx_attendance_employee ON attendance_logs(employee_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_logs(date);
CREATE INDEX IF NOT EXISTS idx_attendance_device ON attendance_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_employee_photos_employee ON employee_photos(employee_id);

-- Insert default roles
INSERT OR IGNORE INTO roles (name) VALUES 
    ('مدير'),
    ('موظف');

-- Insert default permissions
INSERT OR IGNORE INTO permissions (code, name, description) VALUES
    ('manage_employees', 'إدارة الموظفين', 'إضافة وتعديل وحذف بيانات الموظفين'),
    ('manage_departments', 'إدارة الأقسام', 'إضافة وتعديل وحذف الأقسام'),
    ('manage_attendance', 'إدارة الحضور والانصراف', 'تسجيل وتعديل بيانات الحضور والانصراف'),
    ('manage_leaves', 'إدارة الإجازات', 'إدارة طلبات الإجازات والموافقة عليها'),
    ('manage_shifts', 'إدارة الورديات', 'إضافة وتعديل الورديات وجداول العمل'),
    ('view_reports', 'عرض التقارير', 'الوصول إلى تقارير النظام'),
    ('manage_roles', 'إدارة الأدوار', 'إدارة الأدوار والصلاحيات'),
    ('approve_requests', 'اعتماد الطلبات', 'الموافقة على طلبات الإجازات والأذونات');

-- Insert default status types
INSERT OR IGNORE INTO status_types (name, requires_approval, max_days) VALUES 
    ('إجازة سنوية', TRUE, 30),
    ('إجازة مرضية', TRUE, 14),
    ('إجازة طارئة', TRUE, 7),
    ('مهمة عمل', TRUE, NULL),
    ('إجازة بدون راتب', TRUE, NULL);

-- Insert default shift types
INSERT OR IGNORE INTO shift_types (name, start_time, end_time, break_duration, flexible_minutes, overtime_allowed) VALUES 
    ('صباحي', '08:00', '16:00', 60, 15, TRUE),
    ('مسائي', '16:00', '00:00', 60, 15, TRUE),
    ('ليلي', '00:00', '08:00', 60, 15, TRUE);

-- Grant all permissions to manager role
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'مدير'; 