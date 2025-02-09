from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QApplication, QMessageBox, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QProcess
from PyQt6.QtGui import QFont, QGuiApplication, QScreen, QAction
import os
import sys

from .styles import (
    MAIN_WINDOW_STYLE, TAB_WIDGET_STYLE,
    FONT_CONFIG, LAYOUT_MARGINS
)
from .tabs.departments_tab import DepartmentsTab
from .tabs.employees_tab import EmployeesTab
from .tabs.attendance_tab import AttendanceTab
from .tabs.reports_tab import ReportsTab
from .tabs.roles_tab import RolesTab
from .tabs.status_types_tab import StatusTypesTab
from .tabs.shift_types_tab import ShiftTypesTab
from .tabs.leaves_tab import LeavesTab
from .tabs.permissions_tab import PermissionsTab
from .tabs.vacations_tab import VacationsTab
from .tabs.employee_status_tab import EmployeeStatusTab
from .login_dialog import LoginDialog
from .dialogs.change_password_dialog import ChangePasswordDialog
from ..database.departments_db import DepartmentsDatabase
from ..utils.session_manager import SessionManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Get database path
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, 'attendance.db')
        
        # Initialize session manager
        self.session = SessionManager()
        self.db = DepartmentsDatabase(self.db_path)
        self.session.initialize(self.db)
        
        # Show login dialog
        login_dialog = LoginDialog(self.db_path)
        if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
            # User cancelled login
            raise SystemExit
            
        # Start session
        employee_id, role_code, session_id = login_dialog.get_session_info()
        self.session.start_session(employee_id, role_code, session_id)
        
        # Setup UI
        self.setup_ui(self.db_path)
        self.setup_menu()
        
        # Set window properties
        self.setWindowTitle(f"نظام إدارة الحضور والانصراف - {self.session.get_role_name()}")
        self.setGeometry(100, 100, 1200, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # Account menu
        account_menu = menubar.addMenu("الحساب")
        
        # Change password action
        change_password = QAction("تغيير كلمة المرور", self)
        change_password.triggered.connect(self.show_change_password)
        account_menu.addAction(change_password)
        
        # Logout action
        logout = QAction("تسجيل الخروج", self)
        logout.triggered.connect(self.handle_logout)
        account_menu.addAction(logout)
        
        # Admin menu
        if self.session.is_admin:
            admin_menu = menubar.addMenu("إدارة النظام")
            
            # Roles management
            roles = QAction("إدارة الأدوار", self)
            roles.triggered.connect(self.show_roles_tab)
            admin_menu.addAction(roles)
            
            # Permissions management
            permissions = QAction("إدارة الصلاحيات", self)
            permissions.triggered.connect(self.show_permissions_tab)
            admin_menu.addAction(permissions)
        
    def setup_ui(self, db_path: str):
        """Setup the main window UI"""
        # Create tab widget
        tabs = QTabWidget(self)
        self.setCentralWidget(tabs)
        
        # Create tabs based on role
        if self.session.has_permission('MANAGE_ATTENDANCE'):
            attendance_tab = AttendanceTab(self.db)
            tabs.addTab(attendance_tab, "الحضور والانصراف")
            
        if self.session.has_permission('MANAGE_USERS'):
            employees_tab = EmployeesTab(self.db, db_path)
            tabs.addTab(employees_tab, "الموظفين")
            
        if self.session.has_permission('MANAGE_DEPARTMENTS'):
            departments_tab = DepartmentsTab(self.db)
            tabs.addTab(departments_tab, "الأقسام")
            
        if self.session.has_permission('VIEW_REPORTS'):
            reports_tab = ReportsTab(self.db)
            tabs.addTab(reports_tab, "التقارير")
            
        if self.session.has_permission('MANAGE_HR'):
            status_types_tab = StatusTypesTab(self.db)
            tabs.addTab(status_types_tab, "أنواع الحالات")
            
            shift_types_tab = ShiftTypesTab(self.db)
            tabs.addTab(shift_types_tab, "أنواع الورديات")
            
            leaves_tab = LeavesTab(self.db)
            tabs.addTab(leaves_tab, "الإجازات")
            
            vacations_tab = VacationsTab(self.db)
            tabs.addTab(vacations_tab, "العطلات")
            
        # Connect signals between tabs if they exist
        try:
            # توصيل الإشارات الأساسية
            employees_tab.employees_changed.connect(departments_tab.update_combos)
            departments_tab.departments_changed.connect(employees_tab.details_tab.update_combos)
            
            # توصيل إشارة الموظفين الجدد لكل التبويبات ذات الصلة
            if self.session.has_permission('MANAGE_ATTENDANCE'):
                employees_tab.employees_changed.connect(attendance_tab.load_employees)
            
            if self.session.has_permission('MANAGE_HR'):
                employees_tab.employees_changed.connect(status_types_tab.load_status_types)
                employees_tab.employees_changed.connect(shift_types_tab.refresh_table)
            
            # if self.session.has_permission('MANAGE_USERS'):
            #     employees_tab.employees_changed.connect(permissions_tab.load_users)
            
            if self.session.has_permission('VIEW_REPORTS'):
                employees_tab.employees_changed.connect(reports_tab.load_data)
            
        except NameError as e:
            print(f"Signal connection skipped: {e}")
        
    def show_change_password(self):
        """Show the change password dialog"""
        dialog = ChangePasswordDialog(self.db, self.session.employee_id, self)
        dialog.exec()
        
    def handle_logout(self):
        """Handle user logout"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل أنت متأكد من تسجيل الخروج؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # End session
            self.session.end_session()
            
            # Clear remember me token
            login_dialog = LoginDialog(self.db_path)
            login_dialog.clear_remember_me()
            
            # Restart application
            QApplication.quit()
            status = QProcess.startDetached(sys.executable, sys.argv)
            
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل أنت متأكد من الخروج من البرنامج؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # End session
            self.session.end_session()
            event.accept()
        else:
            event.ignore()
            
    def center(self):
        """Center the window on the screen."""
        frame = self.frameGeometry()
        screen = QGuiApplication.primaryScreen().availableGeometry()
        center_point = screen.center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())
        
    def show_roles_tab(self):
        """Show the roles management tab."""
        roles_tab = RolesTab(self.db)
        self.centralWidget().addTab(roles_tab, "إدارة الأدوار")
        self.centralWidget().setCurrentWidget(roles_tab)
        
    def show_permissions_tab(self):
        """Show the permissions management tab."""
        permissions_tab = PermissionsTab(self.db)
        self.centralWidget().addTab(permissions_tab, "إدارة الصلاحيات")
        self.centralWidget().setCurrentWidget(permissions_tab) 