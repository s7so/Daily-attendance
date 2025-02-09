from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from ...utils.password_utils import check_password_complexity
from ...database.employees_db import EmployeesDatabase

class ChangePasswordDialog(QDialog):
    def __init__(self, db: EmployeesDatabase, employee_id: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.employee_id = employee_id
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("تغيير كلمة المرور")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(400)  # Set minimum width for better appearance
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title = QLabel("تغيير كلمة المرور")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2196F3; margin: 10px;")
        layout.addWidget(title)
        
        # Current password
        current_layout = QHBoxLayout()
        current_label = QLabel("كلمة المرور الحالية:")
        self.current_input = QLineEdit()
        self.current_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_input.setPlaceholderText("أدخل كلمة المرور الحالية")
        current_layout.addWidget(self.current_input)
        current_layout.addWidget(current_label)
        
        # New password
        new_layout = QHBoxLayout()
        new_label = QLabel("كلمة المرور الجديدة:")
        self.new_input = QLineEdit()
        self.new_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_input.setPlaceholderText("أدخل كلمة المرور الجديدة")
        new_layout.addWidget(self.new_input)
        new_layout.addWidget(new_label)
        
        # Confirm password
        confirm_layout = QHBoxLayout()
        confirm_label = QLabel("تأكيد كلمة المرور:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("أعد إدخال كلمة المرور الجديدة")
        confirm_layout.addWidget(self.confirm_input)
        confirm_layout.addWidget(confirm_label)
        
        # Requirements label
        requirements = (
            "متطلبات كلمة المرور:\n"
            "- 8 أحرف على الأقل\n"
            "- حرف كبير واحد على الأقل\n"
            "- حرف صغير واحد على الأقل\n"
            "- رقم واحد على الأقل\n"
            "- رمز خاص واحد على الأقل (!@#$%^&*(),.?\":{}|<>)"
        )
        req_label = QLabel(requirements)
        req_label.setStyleSheet("color: gray; font-size: 10pt; margin: 10px;")
        req_label.setWordWrap(True)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("إلغاء")
        self.save_btn = QPushButton("حفظ")
        self.save_btn.setDefault(True)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)
        
        # Add all layouts
        layout.addLayout(current_layout)
        layout.addLayout(new_layout)
        layout.addLayout(confirm_layout)
        layout.addWidget(req_label)
        layout.addLayout(buttons_layout)
        
        # Connect signals
        self.cancel_btn.clicked.connect(self.reject)
        self.save_btn.clicked.connect(self.handle_save)
        
        # Set tab order
        self.setTabOrder(self.current_input, self.new_input)
        self.setTabOrder(self.new_input, self.confirm_input)
        self.setTabOrder(self.confirm_input, self.save_btn)
        
        # Set initial focus
        self.current_input.setFocus()
        
    def handle_save(self):
        current = self.current_input.text()
        new = self.new_input.text()
        confirm = self.confirm_input.text()
        
        # Verify current password
        if not self.db.verify_password(self.employee_id, current):
            QMessageBox.warning(self, "خطأ", "كلمة المرور الحالية غير صحيحة")
            self.current_input.setFocus()
            return
            
        # Check if new password matches confirmation
        if new != confirm:
            QMessageBox.warning(self, "خطأ", "كلمة المرور الجديدة غير متطابقة مع التأكيد")
            self.confirm_input.setFocus()
            return
            
        # Check if new password is same as current
        if current == new:
            QMessageBox.warning(
                self,
                "خطأ",
                "كلمة المرور الجديدة يجب أن تكون مختلفة عن كلمة المرور الحالية"
            )
            self.new_input.setFocus()
            return
            
        # Check password complexity
        is_valid, message = check_password_complexity(new)
        if not is_valid:
            QMessageBox.warning(self, "خطأ", message)
            self.new_input.setFocus()
            return
            
        # Update password
        if self.db.set_user_password(self.employee_id, new):
            QMessageBox.information(
                self,
                "نجاح",
                "تم تغيير كلمة المرور بنجاح\n"
                "سيتم استخدام كلمة المرور الجديدة في تسجيل الدخول القادم"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء تحديث كلمة المرور") 