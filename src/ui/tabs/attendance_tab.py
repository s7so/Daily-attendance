from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QSpinBox,
    QHeaderView, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette
from ...devices.fingertec import FingertecDevice
from ..styles import (
    BUTTON_STYLE, TABLE_STYLE, INPUT_STYLE,
    LABEL_STYLE, GROUP_BOX_STYLE
)
from ...database.departments_db import DepartmentsDatabase

class AttendanceTab(QWidget):
    def __init__(self, db: DepartmentsDatabase):
        super().__init__()
        self.db = db
        self.device = FingertecDevice()
        self.setup_ui()
        self.setup_device_polling()
        
    def setup_ui(self):
        """تهيئة واجهة تسجيل الحضور والانصراف"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        
        # إعدادات جهاز البصمة - قسم مميز
        device_group = QGroupBox("إعدادات جهاز البصمة")
        device_group.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #495057;
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        device_layout = QVBoxLayout(device_group)
        device_layout.setContentsMargins(20, 20, 20, 20)
        device_layout.setSpacing(15)
        
        # معلومات الاتصال
        connection_layout = QHBoxLayout()
        connection_layout.setSpacing(15)
        
        # عنوان IP
        ip_layout = QVBoxLayout()
        ip_label = QLabel("عنوان IP:")
        ip_label.setStyleSheet("""
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        """)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("مثال: 192.168.1.100")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
                color: #495057;
            }
            QLineEdit:focus {
                border: 2px solid #228be6;
                background-color: #f8f9fa;
            }
            QLineEdit::placeholder {
                color: #adb5bd;
            }
        """)
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)
        connection_layout.addLayout(ip_layout, stretch=2)
        
        # رقم المنفذ
        port_layout = QVBoxLayout()
        port_label = QLabel("رقم المنفذ:")
        port_label.setStyleSheet("""
            font-weight: bold;
            color: #495057;
            margin-bottom: 5px;
        """)
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("مثال: 4370")
        self.port_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
                color: #495057;
            }
            QLineEdit:focus {
                border: 2px solid #228be6;
                background-color: #f8f9fa;
            }
            QLineEdit::placeholder {
                color: #adb5bd;
            }
        """)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        connection_layout.addLayout(port_layout, stretch=1)
        
        # أزرار التحكم في الجهاز
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.connect_btn = QPushButton("اتصال بالجهاز")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #228be6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1c7ed6;
            }
            QPushButton:pressed {
                background-color: #1971c2;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        
        self.sync_btn = QPushButton("مزامنة السجلات")
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #40c057;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #37b24d;
            }
            QPushButton:pressed {
                background-color: #2f9e44;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        
        self.disconnect_btn = QPushButton("قطع الاتصال")
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #fa5252;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f03e3e;
            }
            QPushButton:pressed {
                background-color: #e03131;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        
        buttons_layout.addWidget(self.connect_btn)
        buttons_layout.addWidget(self.sync_btn)
        buttons_layout.addWidget(self.disconnect_btn)
        
        # حالة الاتصال
        status_layout = QHBoxLayout()
        status_label = QLabel("حالة الاتصال:")
        status_label.setStyleSheet("""
            font-weight: bold;
            color: #495057;
            font-size: 13px;
        """)
        self.status_label = QLabel("غير متصل")
        self.status_label.setStyleSheet("""
            padding: 8px 16px;
            border-radius: 6px;
            background-color: #fff5f5;
            color: #e03131;
            font-weight: bold;
            font-size: 13px;
        """)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # إضافة كل العناصر إلى مجموعة الجهاز
        device_layout.addLayout(connection_layout)
        device_layout.addLayout(buttons_layout)
        device_layout.addLayout(status_layout)
        
        # إضافة مجموعة الجهاز إلى التخطيط الرئيسي
        main_layout.addWidget(device_group)
        
        # إضافة خط فاصل
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e9ecef;")
        main_layout.addWidget(separator)
        
        # التسجيل اليدوي
        manual_group = QGroupBox("التسجيل اليدوي")
        manual_group.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #495057;
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        manual_layout = QVBoxLayout(manual_group)
        manual_layout.setContentsMargins(20, 20, 20, 20)
        manual_layout.setSpacing(15)
        
        # اختيار الموظف
        emp_layout = QHBoxLayout()
        emp_label = QLabel("الموظف:")
        emp_label.setStyleSheet("""
            font-weight: bold;
            color: #495057;
            font-size: 13px;
        """)
        self.emp_combo = QComboBox()
        self.emp_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
                color: #495057;
                min-width: 250px;
            }
            QComboBox:focus {
                border: 2px solid #228be6;
                background-color: #f8f9fa;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        emp_layout.addWidget(emp_label)
        emp_layout.addWidget(self.emp_combo)
        emp_layout.addStretch()
        
        # أزرار التسجيل
        manual_buttons_layout = QHBoxLayout()
        self.check_in_btn = QPushButton("تسجيل حضور")
        self.check_in_btn.setStyleSheet("""
            QPushButton {
                background-color: #40c057;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #37b24d;
            }
            QPushButton:pressed {
                background-color: #2f9e44;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        
        self.check_out_btn = QPushButton("تسجيل انصراف")
        self.check_out_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f76707;
            }
            QPushButton:pressed {
                background-color: #e8590c;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        
        manual_buttons_layout.addWidget(self.check_in_btn)
        manual_buttons_layout.addWidget(self.check_out_btn)
        manual_buttons_layout.addStretch()
        
        manual_layout.addLayout(emp_layout)
        manual_layout.addLayout(manual_buttons_layout)
        
        main_layout.addWidget(manual_group)
        
        # جدول السجلات
        table_group = QGroupBox("سجلات اليوم")
        table_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #495057;
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        
        table_layout = QVBoxLayout(table_group)
        table_layout.setContentsMargins(20, 20, 20, 20)
        
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(6)
        self.records_table.setHorizontalHeaderLabels([
            "الموظف", "القسم", "الوردية", "وقت الحضور", "وقت الانصراف", "المصدر"
        ])
        self.records_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                gridline-color: #f1f3f5;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px;
                border: none;
                border-right: 1px solid #e9ecef;
                font-weight: bold;
                color: #495057;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f1f3f5;
                color: #495057;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #e7f5ff;
                color: #1864ab;
            }
        """)
        
        table_layout.addWidget(self.records_table)
        main_layout.addWidget(table_group)
        
        # ربط الإشارات
        self.connect_btn.clicked.connect(self.handle_connect)
        self.disconnect_btn.clicked.connect(self.handle_disconnect)
        self.sync_btn.clicked.connect(self.handle_sync)
        self.check_in_btn.clicked.connect(self.handle_check_in)
        self.check_out_btn.clicked.connect(self.handle_check_out)
        
        # تحديث البيانات
        self.load_employees()
        self.refresh_records()
        
        # تحديث السجلات كل دقيقة
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_records)
        self.timer.start(60000)  # 60 seconds
        
        # تعطيل الأزرار في البداية
        self.sync_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(False)
        
    def setup_device_polling(self):
        """إعداد المؤقت لجلب البيانات من الجهاز"""
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_device)
        self.poll_timer.start(5000)  # Poll every 5 seconds
        
    def handle_connect(self):
        """معالجة الاتصال بالجهاز"""
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        
        if not ip:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال عنوان IP")
            return
            
        # TODO: تنفيذ الاتصال بالجهاز
        self.status_label.setText("متصل")
        self.status_label.setStyleSheet("""
            padding: 8px 16px;
            border-radius: 6px;
            background-color: #e8f5e9;
            color: #2e7d32;
            font-weight: bold;
        """)
        
    def handle_disconnect(self):
        """معالجة قطع الاتصال بالجهاز"""
        # TODO: تنفيذ قطع الاتصال
        self.status_label.setText("غير متصل")
        self.status_label.setStyleSheet("""
            padding: 8px 16px;
            border-radius: 6px;
            background-color: #fff5f5;
            color: #e03131;
            font-weight: bold;
        """)
        
    def handle_sync(self):
        """معالجة مزامنة السجلات"""
        try:
            if not self.device.connected:
                raise Exception("الجهاز غير متصل")
                
            # جلب بيانات الموظفين من الجهاز
            employees = self.device.get_all_users()
            
            for emp in employees:
                # جلب صورة الموظف من الجهاز
                photo = self.device.get_user_photo(emp['id'])
                if photo:
                    # حفظ الصورة في قاعدة البيانات
                    self.db.save_employee_photo(emp['id'], photo)
                    
            # جلب سجلات الحضور
            today = datetime.now()
            logs = self.device.get_attendance_logs(today, today)
            
            # تحديث قاعدة البيانات
            for log in logs:
                self.db.add_attendance(
                    employee_id=log['employee_id'],
                    timestamp=log['timestamp'],
                    type=log['type'],
                    source='device'
                )
                
            self.refresh_records()
            QMessageBox.information(self, "نجاح", "تمت المزامنة بنجاح")
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "خطأ",
                f"فشل المزامنة: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
        
    def handle_check_in(self):
        """معالجة تسجيل الحضور"""
        employee_id = self.emp_combo.currentData()
        if not employee_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار الموظف")
            return
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.db.add_attendance(employee_id, now, 'check_in', 'manual'):
            self.refresh_records()
            QMessageBox.information(self, "نجاح", "تم تسجيل الحضور بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "فشل تسجيل الحضور")
            
    def handle_check_out(self):
        """معالجة تسجيل الانصراف"""
        employee_id = self.emp_combo.currentData()
        if not employee_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار الموظف")
            return
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.db.add_attendance(employee_id, now, 'check_out', 'manual'):
            self.refresh_records()
            QMessageBox.information(self, "نجاح", "تم تسجيل الانصراف بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "فشل تسجيل الانصراف")
            
    def load_employees(self):
        """تحميل قائمة الموظفين"""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
    def set_row_color(self, row: int, color: QColor):
        """تعيين لون صف في الجدول"""
        for col in range(self.records_table.columnCount()):
            item = self.records_table.item(row, col)
            if item:
                item.setBackground(color)

    def refresh_records(self):
        """تحديث جدول سجلات الحضور"""
        try:
            records = self.db.get_today_attendance()
            self.records_table.setRowCount(len(records))
            
            for i, record in enumerate(records):
                # Get department name from either field
                department = record.get('department_name') or record.get('department', '')
                
                # إنشاء عناصر الجدول مع تعيين المحاذاة للوسط
                items = [
                    (str(record['employee_id']), Qt.AlignmentFlag.AlignCenter),
                    (str(record['name']), Qt.AlignmentFlag.AlignRight),
                    (str(department), Qt.AlignmentFlag.AlignRight),
                    (str(record['check_in_time'] or ''), Qt.AlignmentFlag.AlignCenter),
                    (str(record['check_out_time'] or ''), Qt.AlignmentFlag.AlignCenter),
                    (str(record['shift_name'] or ''), Qt.AlignmentFlag.AlignRight)
                ]
                
                for col, (text, alignment) in enumerate(items):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(alignment)
                    self.records_table.setItem(i, col, item)
                
                # تلوين الصفوف حسب حالة التسجيل
                if record['check_out_time']:
                    self.set_row_color(i, QColor(200, 255, 200))  # أخضر فاتح للمنصرفين
                elif record['check_in_time']:
                    self.set_row_color(i, QColor(255, 255, 200))  # أصفر فاتح للحاضرين
            
            # تعديل حجم الأعمدة لتناسب المحتوى
            self.records_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error refreshing records: {str(e)}")
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء تحديث السجلات")
        
    def poll_device(self):
        """Poll device for new records"""
        if not self.device.connected:
            return
            
        try:
            records = self.device.get_new_records()
            for record in records:
                self.db.add_attendance_record(
                    employee_id=record['employee_id'],
                    date=record['date'],
                    time=record['time'],
                    device_id=self.device.device_id
                )
            self.refresh_records()
        except Exception as e:
            print(f"Error polling device: {e}")
            
    def update_employees_list(self):
        """تحديث قائمة الموظفين في الكومبو بوكس"""
        current_emp = self.emp_combo.currentData()  # حفظ الموظف المحدد حالياً
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        
        # جلب كل الموظفين
        employees = self.db.get_all_employees()
        for emp in employees:
            self.emp_combo.addItem(f"{emp['name']} ({emp['department_name']})", emp['id'])
            
        # استعادة الموظف المحدد إذا كان موجوداً
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index) 