from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QStackedWidget,
    QWidget
)
from PyQt6.QtCore import Qt
from ...utils.password_utils import check_password_complexity
from ...database.employees_db import EmployeesDatabase

class ResetPasswordDialog(QDialog):
    def __init__(self, db: EmployeesDatabase, parent=None):
        super().__init__(parent)
        self.db = db
        self.token = None
        self.employee_id = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("إعادة تعيين كلمة المرور")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(400)  # Set minimum width for better appearance
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create stacked widget for multiple steps
        self.stacked = QStackedWidget()
        
        # Step 1: Enter employee ID
        step1 = QWidget()
        step1_layout = QVBoxLayout()
        step1.setLayout(step1_layout)
        
        # Add step indicator
        step1_indicator = QLabel("الخطوة 1 من 3: إدخال رقم الموظف")
        step1_indicator.setStyleSheet("font-weight: bold; color: #2196F3;")
        step1_layout.addWidget(step1_indicator)
        
        id_layout = QHBoxLayout()
        id_label = QLabel("رقم الموظف:")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("أدخل رقم الموظف")
        id_layout.addWidget(self.id_input)
        id_layout.addWidget(id_label)
        
        step1_buttons = QHBoxLayout()
        self.cancel_btn1 = QPushButton("إلغاء")
        self.next_btn = QPushButton("التالي")
        self.next_btn.setDefault(True)
        step1_buttons.addWidget(self.cancel_btn1)
        step1_buttons.addWidget(self.next_btn)
        
        step1_layout.addLayout(id_layout)
        step1_layout.addLayout(step1_buttons)
        
        # Step 2: Enter reset token
        step2 = QWidget()
        step2_layout = QVBoxLayout()
        step2.setLayout(step2_layout)
        
        # Add step indicator
        step2_indicator = QLabel("الخطوة 2 من 3: إدخال رمز التحقق")
        step2_indicator.setStyleSheet("font-weight: bold; color: #2196F3;")
        step2_layout.addWidget(step2_indicator)
        
        token_layout = QHBoxLayout()
        token_label = QLabel("رمز إعادة التعيين:")
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("أدخل رمز إعادة التعيين")
        token_layout.addWidget(self.token_input)
        token_layout.addWidget(token_label)
        
        step2_buttons = QHBoxLayout()
        self.back_btn = QPushButton("رجوع")
        self.verify_btn = QPushButton("تحقق")
        self.verify_btn.setDefault(True)
        step2_buttons.addWidget(self.back_btn)
        step2_buttons.addWidget(self.verify_btn)
        
        step2_layout.addLayout(token_layout)
        step2_layout.addLayout(step2_buttons)
        
        # Step 3: Enter new password
        step3 = QWidget()
        step3_layout = QVBoxLayout()
        step3.setLayout(step3_layout)
        
        # Add step indicator
        step3_indicator = QLabel("الخطوة 3 من 3: إدخال كلمة المرور الجديدة")
        step3_indicator.setStyleSheet("font-weight: bold; color: #2196F3;")
        step3_layout.addWidget(step3_indicator)
        
        new_layout = QHBoxLayout()
        new_label = QLabel("كلمة المرور الجديدة:")
        self.new_input = QLineEdit()
        self.new_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_input.setPlaceholderText("أدخل كلمة المرور الجديدة")
        new_layout.addWidget(self.new_input)
        new_layout.addWidget(new_label)
        
        confirm_layout = QHBoxLayout()
        confirm_label = QLabel("تأكيد كلمة المرور:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("أعد إدخال كلمة المرور الجديدة")
        confirm_layout.addWidget(self.confirm_input)
        confirm_layout.addWidget(confirm_label)
        
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
        
        step3_buttons = QHBoxLayout()
        self.cancel_btn3 = QPushButton("إلغاء")
        self.save_btn = QPushButton("حفظ")
        self.save_btn.setDefault(True)
        step3_buttons.addWidget(self.cancel_btn3)
        step3_buttons.addWidget(self.save_btn)
        
        step3_layout.addLayout(new_layout)
        step3_layout.addLayout(confirm_layout)
        step3_layout.addWidget(req_label)
        step3_layout.addLayout(step3_buttons)
        
        # Add steps to stacked widget
        self.stacked.addWidget(step1)
        self.stacked.addWidget(step2)
        self.stacked.addWidget(step3)
        
        layout.addWidget(self.stacked)
        
        # Connect signals
        self.cancel_btn1.clicked.connect(self.reject)
        self.cancel_btn3.clicked.connect(self.reject)
        self.next_btn.clicked.connect(self.handle_next)
        self.back_btn.clicked.connect(lambda: self.stacked.setCurrentIndex(0))
        self.verify_btn.clicked.connect(self.handle_verify)
        self.save_btn.clicked.connect(self.handle_save)
        
        # Set tab order
        self.setTabOrder(self.id_input, self.next_btn)
        self.setTabOrder(self.token_input, self.verify_btn)
        self.setTabOrder(self.new_input, self.confirm_input)
        self.setTabOrder(self.confirm_input, self.save_btn)
        
    def handle_next(self):
        employee_id = self.id_input.text().strip()
        if not employee_id:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال رقم الموظف")
            self.id_input.setFocus()
            return
            
        # Create reset token
        token = self.db.create_password_reset_token(employee_id)
        if not token:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الموظف")
            self.id_input.setFocus()
            return
            
        # Show token to user (in real app, this would be sent via email/SMS)
        QMessageBox.information(
            self,
            "رمز إعادة التعيين",
            f"تم إنشاء رمز إعادة التعيين: {token}\n\n"
            "الرجاء الاحتفاظ به لاستخدامه في الخطوة التالية.\n"
            "ملاحظة: في التطبيق الفعلي، سيتم إرسال هذا الرمز عبر البريد الإلكتروني أو الرسائل القصيرة."
        )
        
        self.employee_id = employee_id
        self.stacked.setCurrentIndex(1)
        self.token_input.setFocus()
        
    def handle_verify(self):
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "خطأ", "الرجاء إدخال رمز إعادة التعيين")
            self.token_input.setFocus()
            return
            
        # Verify token
        employee_id = self.db.verify_reset_token(token)
        if not employee_id or employee_id != self.employee_id:
            QMessageBox.warning(self, "خطأ", "رمز إعادة التعيين غير صالح")
            self.token_input.setFocus()
            return
            
        self.token = token
        self.stacked.setCurrentIndex(2)
        self.new_input.setFocus()
        
    def handle_save(self):
        new = self.new_input.text()
        confirm = self.confirm_input.text()
        
        # Check if new password matches confirmation
        if new != confirm:
            QMessageBox.warning(self, "خطأ", "كلمة المرور الجديدة غير متطابقة مع التأكيد")
            self.confirm_input.setFocus()
            return
            
        # Check password complexity
        is_valid, message = check_password_complexity(new)
        if not is_valid:
            QMessageBox.warning(self, "خطأ", message)
            self.new_input.setFocus()
            return
            
        # Update password and clear reset token
        if self.db.set_user_password(self.employee_id, new):
            self.db.clear_reset_token(self.employee_id)
            QMessageBox.information(
                self,
                "نجاح",
                "تم إعادة تعيين كلمة المرور بنجاح\n"
                "يمكنك الآن تسجيل الدخول باستخدام كلمة المرور الجديدة"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء تحديث كلمة المرور") 