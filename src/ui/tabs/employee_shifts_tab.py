from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem,
    QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from ...database.departments_db import DepartmentsDatabase

class EmployeeShiftsTab(QWidget):
    def __init__(self, db: DepartmentsDatabase):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # منطقة الإضافة
        add_group = QHBoxLayout()
        
        # اختيار الموظف
        self.emp_combo = QComboBox()
        self.emp_combo.setMinimumWidth(200)
        add_group.addWidget(QLabel("الموظف:"))
        add_group.addWidget(self.emp_combo)
        
        # اختيار الوردية
        self.shift_combo = QComboBox()
        self.shift_combo.setMinimumWidth(200)
        add_group.addWidget(QLabel("الوردية:"))
        add_group.addWidget(self.shift_combo)
        
        # تاريخ البداية
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        add_group.addWidget(QLabel("من تاريخ:"))
        add_group.addWidget(self.start_date)
        
        # تاريخ النهاية
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        add_group.addWidget(QLabel("إلى تاريخ:"))
        add_group.addWidget(self.end_date)
        
        # زر الإضافة
        add_btn = QPushButton("إضافة")
        add_btn.clicked.connect(self.add_shift)
        add_group.addWidget(add_btn)
        
        add_group.addStretch()
        layout.addLayout(add_group)
        
        # جدول الورديات
        self.shifts_table = QTableWidget()
        self.shifts_table.setColumnCount(6)
        self.shifts_table.setHorizontalHeaderLabels([
            "الموظف", "الوردية", "وقت البداية",
            "وقت النهاية", "من تاريخ", "إلى تاريخ"
        ])
        layout.addWidget(self.shifts_table)
        
        # تحميل البيانات
        self.load_data()
        
    def load_data(self):
        """تحميل البيانات الأولية"""
        # تحميل الموظفين
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            # Handle both department and department_name fields
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # تحميل الورديات
        if hasattr(self.db, 'get_all_shift_types'):
            shifts = self.db.get_all_shift_types()
        else:
            shifts = DepartmentsDatabase(self.db.db_path).get_all_shift_types()
        self.shift_combo.clear()
        self.shift_combo.addItem("-- اختر الوردية --", None)
        for shift in shifts:
            self.shift_combo.addItem(shift['name'], shift['id'])
            
        # تحديث الجدول
        self.refresh_shifts()
        
    def refresh_shifts(self):
        """تحديث جدول الورديات"""
        employee_id = self.emp_combo.currentData()
        if not employee_id:
            return
            
        shifts = self.db.get_employee_shifts(employee_id)
        self.shifts_table.setRowCount(len(shifts))
        
        for i, shift in enumerate(shifts):
            items = [
                QTableWidgetItem(self.emp_combo.currentText()),
                QTableWidgetItem(shift['shift_name']),
                QTableWidgetItem(shift['shift_start']),
                QTableWidgetItem(shift['shift_end']),
                QTableWidgetItem(shift['start_date']),
                QTableWidgetItem(shift['end_date'] or '')
            ]
            
            for j, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.shifts_table.setItem(i, j, item)
                
    def add_shift(self):
        """إضافة وردية جديدة"""
        employee_id = self.emp_combo.currentData()
        shift_type_id = self.shift_combo.currentData()
        
        if not employee_id or not shift_type_id:
            QMessageBox.warning(
                self,
                "تنبيه",
                "الرجاء اختيار الموظف والوردية",
                QMessageBox.StandardButton.Ok
            )
            return
            
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        
        if self.db.assign_employee_shift(employee_id, shift_type_id, start_date, end_date):
            self.refresh_shifts()
            QMessageBox.information(
                self,
                "نجاح",
                "تم إضافة الوردية بنجاح",
                QMessageBox.StandardButton.Ok
            )
        else:
            QMessageBox.warning(
                self,
                "خطأ",
                "فشل إضافة الوردية",
                QMessageBox.StandardButton.Ok
            ) 