from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QCheckBox,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from ..database.employees_db import EmployeesDatabase
from .dialogs.reset_password_dialog import ResetPasswordDialog
from ..utils.password_utils import check_password_complexity
import os

class LoginDialog(QDialog):
    def __init__(self, db_path: str, parent=None):
        super().__init__(parent)
        self.db = EmployeesDatabase(db_path)
        self.logged_in_employee = None
        self.session_id = None
        self.role_code = None
        self.role_id = None
        
        # Verify database and admin account
        self.db.debug_admin_password()
        
        self.setup_ui()
        self.check_remember_me()
        
    def setup_ui(self):
        self.setWindowTitle("تسجيل الدخول")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 14pt;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 4px;
                border: none;
                font-size: 12pt;
            }
            QPushButton#loginBtn {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                font-size: 14pt;
            }
            QPushButton#loginBtn:hover {
                background-color: #1976D2;
            }
            QPushButton#loginBtn:pressed {
                background-color: #0D47A1;
            }
            QPushButton#resetBtn {
                background-color: transparent;
                color: #2196F3;
                text-decoration: underline;
            }
            QPushButton#resetBtn:hover {
                color: #1976D2;
            }
            QLabel#titleLabel {
                font-size: 24pt;
                font-weight: bold;
                color: #2196F3;
                margin-bottom: 20px;
            }
        """)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("نظام إدارة الحضور والانصراف")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Form container
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 30px;
            }
        """)
        form_layout = QVBoxLayout()
        form_container.setLayout(form_layout)
        
        # Password input
        password_layout = QVBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setMinimumHeight(50)
        password_layout.addWidget(self.password_input)
        
        # Remember me checkbox
        self.remember_me = QCheckBox("تذكرني")
        self.remember_me.setStyleSheet("""
            QCheckBox {
                margin-top: 10px;
                margin-bottom: 10px;
                font-size: 12pt;
            }
        """)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.login_btn = QPushButton("دخول")
        self.login_btn.setObjectName("loginBtn")
        self.login_btn.setMinimumHeight(50)
        self.reset_btn = QPushButton("نسيت كلمة المرور؟")
        self.reset_btn.setObjectName("resetBtn")
        self.cancel_btn = QPushButton("إلغاء")
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.reset_btn)
        buttons_layout.addWidget(self.login_btn)
        
        # Add all layouts to form container
        form_layout.addLayout(password_layout)
        form_layout.addWidget(self.remember_me)
        form_layout.addLayout(buttons_layout)
        
        # Add form container to main layout
        layout.addWidget(form_container)
        
        # Connect signals
        self.login_btn.clicked.connect(self.handle_login)
        self.reset_btn.clicked.connect(self.handle_reset)
        self.cancel_btn.clicked.connect(self.reject)
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Set initial focus
        self.password_input.setFocus()
        
    def check_remember_me(self):
        """التحقق من وجود توكن تذكرني وتسجيل الدخول تلقائياً إذا كان صالحاً"""
        try:
            # محاولة قراءة التوكن من الملف
            token_file = os.path.join(os.path.dirname(self.db.db_path), "remember_me.token")
            if not os.path.exists(token_file):
                return
                
            with open(token_file, "r") as f:
                token = f.read().strip()
                if not token:
                    return
                    
            # جلب معلومات الجهاز
            device_info = self.get_device_info()
                    
            # التحقق من صحة التوكن
            result = self.db.verify_remember_me_token(token, device_info)
            if result:
                employee_id, role_code, role_id = result
                self.logged_in_employee = employee_id
                self.role_code = role_code
                self.role_id = role_id
                
                # إنشاء جلسة جديدة
                self.create_session()
                
                # إظهار رسالة ترحيب
                role_names = {
                    'ADMIN': 'مدير النظام',
                    'HR': 'مسؤول الموارد البشرية',
                    'EMPLOYEE': 'موظف'
                }
                QMessageBox.information(
                    self,
                    "مرحباً",
                    f"تم تسجيل دخولك تلقائياً\n"
                    f"الدور: {role_names.get(role_code, role_code)}"
                )
                
                self.accept()
            else:
                # حذف الملف إذا كان التوكن غير صالح
                os.remove(token_file)
                
        except Exception as e:
            print(f"خطأ في التحقق من توكن تذكرني: {str(e)}")
            
    def save_remember_me(self, employee_id: str):
        """حفظ توكن تذكرني إذا تم اختيار الخيار"""
        if self.remember_me.isChecked():
            try:
                # إنشاء توكن جديد مع معلومات الجهاز
                device_info = self.get_device_info()
                ip_address = self.get_ip_address()
                
                token = self.db.create_remember_me_token(
                    employee_id,
                    device_info=device_info,
                    ip_address=ip_address
                )
                
                if token:
                    # حفظ التوكن في ملف
                    token_file = os.path.join(os.path.dirname(self.db.db_path), "remember_me.token")
                    with open(token_file, "w") as f:
                        f.write(token)
                        
            except Exception as e:
                print(f"خطأ في حفظ توكن تذكرني: {str(e)}")
                
    def clear_remember_me(self):
        """حذف توكن تذكرني"""
        try:
            # حذف الملف
            token_file = os.path.join(os.path.dirname(self.db.db_path), "remember_me.token")
            if os.path.exists(token_file):
                os.remove(token_file)
                
            # حذف التوكن من قاعدة البيانات
            if self.logged_in_employee:
                device_info = self.get_device_info()
                self.db.clear_remember_me_tokens(
                    employee_id=self.logged_in_employee,
                    device_info=device_info
                )
                
        except Exception as e:
            print(f"خطأ في حذف توكن تذكرني: {str(e)}")
            
    def get_device_info(self) -> str:
        """الحصول على معلومات الجهاز"""
        try:
            import platform
            import uuid
            
            system = platform.system()
            release = platform.release()
            machine = platform.machine()
            node = platform.node()
            
            # إنشاء معرف فريد للجهاز
            mac = uuid.getnode()
            
            return f"{system}-{release}-{machine}-{node}-{mac}"
        except:
            return None
            
    def get_ip_address(self) -> str:
        """الحصول على عنوان IP"""
        try:
            import socket
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return None
            
    def create_session(self):
        """Create a new session"""
        self.session_id = self.db.create_session(self.logged_in_employee, self.role_id)
            
    def handle_login(self):
        password = self.password_input.text()
        
        if not password:
            QMessageBox.warning(
                self,
                "خطأ",
                "الرجاء إدخال كلمة المرور"
            )
            self.password_input.setFocus()
            return
            
        # Try to reset admin password if login fails
        result = self.db.verify_password_only(password)
        if not result and password == "Admin@2024":
            reply = QMessageBox.question(
                self,
                "إعادة تعيين كلمة المرور",
                "هل تريد إعادة تعيين كلمة مرور المدير إلى القيمة الافتراضية؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.db.reset_admin_password():
                    QMessageBox.information(
                        self,
                        "نجاح",
                        "تم إعادة تعيين كلمة مرور المدير\n"
                        "حاول تسجيل الدخول مرة أخرى"
                    )
                    self.password_input.clear()
                    self.password_input.setFocus()
                    return
                    
        # Verify password and get employee ID and role
        if result:
            employee_id, role_code, role_id = result
            self.logged_in_employee = employee_id
            self.role_code = role_code
            self.role_id = role_id
            
            # Create session
            self.create_session()
            
            # Record login attempt
            self.db.record_login_attempt(employee_id, True)
            
            # Save remember me token if checked
            self.save_remember_me(employee_id)
            
            # Show welcome message based on role
            role_names = {
                'ADMIN': 'مدير النظام',
                'HR': 'مسؤول الموارد البشرية',
                'EMPLOYEE': 'موظف'
            }
            QMessageBox.information(
                self,
                "مرحباً",
                f"مرحباً بك في النظام\n"
                f"الدور: {role_names.get(role_code, role_code)}"
            )
            
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "خطأ",
                "كلمة المرور غير صحيحة\n\n"
                "ملاحظة: إذا كنت تحاول الدخول كمدير لأول مرة،\n"
                "جرب كلمة المرور الافتراضية: Admin@2024"
            )
            self.password_input.clear()
            self.password_input.setFocus()
            
    def handle_reset(self):
        dialog = ResetPasswordDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "نجاح",
                "تم إعادة تعيين كلمة المرور بنجاح\n"
                "يمكنك الآن تسجيل الدخول باستخدام كلمة المرور الجديدة"
            )
            self.password_input.clear()
            self.password_input.setFocus()
            
    def get_session_info(self) -> tuple:
        """Return session information (employee_id, role_code, session_id)"""
        return (self.logged_in_employee, self.role_code, self.session_id) 