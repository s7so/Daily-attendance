from typing import Optional, List
from ..database.employees_db import EmployeesDatabase

class SessionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.employee_id = None
            self.role_code = None
            self.session_id = None
            self.permissions = []
            self.db = None
            
    def initialize(self, db: EmployeesDatabase):
        """Initialize the session manager with database connection"""
        print("Initializing session manager...")
        self.db = db
        # Clean up expired sessions on startup
        self.db.cleanup_expired_sessions()
        print("Session manager initialized")
        
    def start_session(self, employee_id: str, role_code: str, session_id: str):
        """Start a new session"""
        print(f"Starting session for employee {employee_id} with role {role_code}")
        self.employee_id = employee_id
        self.role_code = role_code
        self.session_id = session_id
        self._load_permissions()
        print("Session started successfully")
        
    def end_session(self):
        """End the current session"""
        print("Ending session...")
        if self.session_id and self.db:
            self.db.end_session(self.session_id)
            self.employee_id = None
            self.role_code = None
            self.session_id = None
            self.permissions = []
            print("Session ended")
        
    def verify_session(self) -> bool:
        """Verify if the current session is valid"""
        print("Verifying session...")
        if not all([self.session_id, self.db]):
            print("Missing session ID or database connection")
            return False
            
        result = self.db.verify_session(self.session_id)
        if not result:
            print("Session verification failed")
            self.end_session()
            return False
            
        employee_id, role_code = result
        if employee_id != self.employee_id or role_code != self.role_code:
            print("Session user mismatch")
            self.end_session()
            return False
            
        print("Session verified successfully")
        return True
        
    def _load_permissions(self):
        """Load user permissions based on role"""
        print("Loading permissions...")
        if self.db and self.role_code:
            cursor = self.db.execute_query(
                """
                SELECT id, code FROM roles WHERE code = ?
                """,
                (self.role_code,)
            )
            result = cursor.fetchone()
            if result:
                print(f"Loading permissions for role {result['id']} ({self.role_code})")
                self.permissions = self.db.get_user_permissions(result['id'])
                print(f"Loaded permissions: {self.permissions}")
            else:
                print(f"Role not found: {self.role_code}")
        else:
            print("Missing database connection or role code")
                
    def has_permission(self, permission_code: str) -> bool:
        """Check if user has a specific permission"""
        if self.role_code == 'ADMIN':
            return True
        has_perm = permission_code in self.permissions
        print(f"Permission check: {permission_code} -> {has_perm}")
        return has_perm
        
    def require_permission(self, permission_code: str):
        """Decorator to require a specific permission"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.has_permission(permission_code):
                    raise PermissionError(f"ليس لديك صلاحية: {permission_code}")
                return func(*args, **kwargs)
            return wrapper
        return decorator
        
    @property
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.role_code == 'ADMIN'
        
    @property
    def is_hr(self) -> bool:
        """Check if current user is HR"""
        return self.role_code == 'HR'
        
    @property
    def is_employee(self) -> bool:
        """Check if current user is regular employee"""
        return self.role_code == 'EMPLOYEE'
        
    def get_role_name(self) -> str:
        """Get the Arabic name of the current role"""
        role_names = {
            'ADMIN': 'مدير النظام',
            'HR': 'مسؤول الموارد البشرية',
            'EMPLOYEE': 'موظف'
        }
        return role_names.get(self.role_code, self.role_code or '') 