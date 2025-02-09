from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QMessageBox, QComboBox, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from ...database.employees_db import EmployeesDatabase
from ...database.departments_db import DepartmentsDatabase
from datetime import datetime
from .employee_status_tab import EmployeeStatusTab
from .employee_shifts_tab import EmployeeShiftsTab
from ...database.database import Database

class EmployeeDetailsTab(QWidget):
    employees_changed = pyqtSignal()  # Signal to notify when employees list changes
    
    def __init__(self, db: DepartmentsDatabase, db_path: str):
        super().__init__()
        self.db = db
        self.emp_db = EmployeesDatabase(db_path)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Employee details input
        form_layout = QVBoxLayout()
        
        # ID input with generate button
        id_layout = QHBoxLayout()
        id_label = QLabel("رقم الموظف:")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("أدخل رقم الموظف أو اضغط على زر التوليد التلقائي")
        self.generate_id_btn = QPushButton("توليد رقم تلقائي")
        id_layout.addWidget(self.generate_id_btn)
        id_layout.addWidget(self.id_input)
        id_layout.addWidget(id_label)
        
        # Name input
        name_layout = QHBoxLayout()
        name_label = QLabel("اسم الموظف:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("أدخل اسم الموظف")
        name_layout.addWidget(self.name_input)
        name_layout.addWidget(name_label)
        
        # Department selection
        dept_layout = QHBoxLayout()
        dept_label = QLabel("القسم:")
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("-- اختر القسم --", None)
        dept_layout.addWidget(self.dept_combo)
        dept_layout.addWidget(dept_label)
        
        # Role selection
        role_layout = QHBoxLayout()
        role_label = QLabel("الدور الوظيفي:")
        self.role_combo = QComboBox()
        self.role_combo.addItem("-- اختر الدور الوظيفي --", None)
        role_layout.addWidget(self.role_combo)
        role_layout.addWidget(role_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("إضافة موظف")
        self.update_btn = QPushButton("تحديث بيانات")
        self.delete_btn = QPushButton("حذف موظف")
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.add_btn)
        
        # Employees table
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(4)
        self.employees_table.setHorizontalHeaderLabels(
            ["الدور الوظيفي", "القسم", "اسم الموظف", "رقم الموظف"]
        )
        
        # Add all layouts
        form_layout.addLayout(id_layout)
        form_layout.addLayout(name_layout)
        form_layout.addLayout(dept_layout)
        form_layout.addLayout(role_layout)
        
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.employees_table)
        
        # Connect signals
        self.generate_id_btn.clicked.connect(self.generate_employee_id)
        self.add_btn.clicked.connect(self.handle_add)
        self.update_btn.clicked.connect(self.handle_update)
        self.delete_btn.clicked.connect(self.handle_delete)
        self.employees_table.itemClicked.connect(self.handle_table_click)
        
        # Initial updates
        self.update_combos()
        self.update_employees_table()
        
    def update_combos(self):
        """Update department and role combo boxes."""
        # Update departments combo
        current_dept = self.dept_combo.currentData()  # Save current selection
        self.dept_combo.clear()
        self.dept_combo.addItem("-- اختر القسم --", None)
        departments = self.db.get_all_departments()
        for dept in departments:
            self.dept_combo.addItem(dept['name'], dept['code'])
        
        # Restore previous selection if it still exists
        if current_dept:
            index = self.dept_combo.findData(current_dept)
            if index >= 0:
                self.dept_combo.setCurrentIndex(index)
            
        # Update roles combo
        current_role = self.role_combo.currentData()  # Save current selection
        self.role_combo.clear()
        self.role_combo.addItem("-- اختر الدور الوظيفي --", None)
        roles = self.db.get_roles()
        for role in roles:
            self.role_combo.addItem(role['name'], role['id'])
            
        # Restore previous selection if it still exists
        if current_role:
            index = self.role_combo.findData(current_role)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
                
    def generate_employee_id(self):
        """Generate and set the next available employee ID."""
        try:
            next_id = self.emp_db.get_next_employee_id()
            self.id_input.setText(next_id)
            self.id_input.setStyleSheet("background-color: #e8f0fe;")  # Light blue background
            QMessageBox.information(
                self,
                "تم توليد الرقم",
                f"تم توليد رقم موظف جديد: {next_id}\n"
                f"(السنة: {next_id[:4]}, الرقم التسلسلي: {next_id[4:]})"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "خطأ",
                "حدث خطأ أثناء توليد رقم الموظف. الرجاء المحاولة مرة أخرى."
            )
            
    def handle_add(self):
        employee_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        department_code = self.dept_combo.currentData()
        role_id = self.role_combo.currentData()
        
        # Validate inputs
        if not employee_id or not name or not department_code or not role_id:
            QMessageBox.warning(self, "تنبيه", "جميع الحقول مطلوبة")
            return
            
        if not employee_id.isdigit() or len(employee_id) != 8:
            QMessageBox.warning(
                self, 
                "تنبيه", 
                "صيغة رقم الموظف غير صحيحة\n"
                "يجب أن يكون الرقم 8 أرقام بصيغة: YYYYXXXX\n"
                "حيث YYYY هي السنة وXXXX هو الرقم التسلسلي"
            )
            return
            
        current_year = str(datetime.now().year)
        if not employee_id.startswith(current_year):
            QMessageBox.warning(
                self, 
                "تنبيه", 
                f"يجب أن يبدأ رقم الموظف بالسنة الحالية: {current_year}"
            )
            return
            
        # Try to add employee
        if self.emp_db.add_employee(employee_id, name, department_code, role_id):
            # Set initial password (using employee ID as initial password)
            self.emp_db.set_user_password(employee_id, employee_id)
            
            self.clear_inputs()
            self.update_employees_table()
            self.employees_changed.emit()  # Emit signal when employee is added
            QMessageBox.information(
                self, 
                "نجاح", 
                f"تم إضافة الموظف بنجاح\n"
                f"الرقم: {employee_id}\n"
                f"الاسم: {name}\n"
                f"القسم: {self.dept_combo.currentText()}\n"
                f"الدور: {self.role_combo.currentText()}\n\n"
                f"كلمة المرور الأولية هي نفس رقم الموظف: {employee_id}"
            )
        else:
            QMessageBox.warning(self, "خطأ", "رقم الموظف موجود بالفعل")
            
    def handle_update(self):
        employee_id = self.id_input.text().strip()
        name = self.name_input.text().strip()
        department_code = self.dept_combo.currentData()
        role_id = self.role_combo.currentData()
        
        if not employee_id or not name or not department_code or not role_id:
            QMessageBox.warning(self, "تنبيه", "جميع الحقول مطلوبة")
            return
            
        if self.emp_db.update_employee(employee_id, name, department_code, role_id):
            self.clear_inputs()
            self.update_employees_table()
            self.employees_changed.emit()  # Emit signal when employee is updated
            QMessageBox.information(self, "نجاح", "تم تحديث بيانات الموظف بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الموظف")
            
    def handle_delete(self):
        employee_id = self.id_input.text().strip()
        if not employee_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف أولاً")
            return
            
        reply = QMessageBox.question(
            self, 
            "تأكيد", 
            "هل أنت متأكد من حذف هذا الموظف؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.emp_db.delete_employee(employee_id):
                self.clear_inputs()
                self.update_employees_table()
                self.update_combos()  # Update combos as this might affect department managers
                self.employees_changed.emit()  # Emit signal when employee is deleted
                QMessageBox.information(self, "نجاح", "تم حذف الموظف بنجاح")
            else:
                QMessageBox.warning(self, "خطأ", "لم يتم العثور على الموظف")
                
    def handle_table_click(self, item):
        row = item.row()
        self.id_input.setText(self.employees_table.item(row, 3).text())
        self.name_input.setText(self.employees_table.item(row, 0).text())
        
        # Find and set department in combo
        dept_name = self.employees_table.item(row, 1).text()
        for i in range(self.dept_combo.count()):
            if self.dept_combo.itemText(i) == dept_name:
                self.dept_combo.setCurrentIndex(i)
                break
                
        # Find and set role in combo
        role_name = self.employees_table.item(row, 2).text()
        for i in range(self.role_combo.count()):
            if self.role_combo.itemText(i) == role_name:
                self.role_combo.setCurrentIndex(i)
                break
        
    def clear_inputs(self):
        self.id_input.setText("")
        self.name_input.setText("")
        self.dept_combo.setCurrentIndex(0)
        self.role_combo.setCurrentIndex(0)
        self.id_input.setStyleSheet("")  # Reset background color
        
    def update_employees_table(self):
        """Update the employees table with fresh data."""
        employees = self.db.get_all_employees()
        self.employees_table.setRowCount(len(employees))
        
        for row, emp in enumerate(employees):
            # Get department name from either field
            department = emp.get('department_name') or emp.get('department', '')
            # Get role name from either field
            role = emp.get('role_name') or emp.get('role', '')
            
            self.employees_table.setItem(row, 0, QTableWidgetItem(emp['name']))
            self.employees_table.setItem(row, 1, QTableWidgetItem(department))
            self.employees_table.setItem(row, 2, QTableWidgetItem(role))
            self.employees_table.setItem(row, 3, QTableWidgetItem(emp['id']))

class EmployeesTab(QWidget):
    employees_changed = pyqtSignal()  # Signal to notify when employees list changes
    
    def __init__(self, db: Database, db_path: str):
        super().__init__()
        self.db = db
        self.emp_db = EmployeesDatabase(db_path)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create tabs
        tabs = QTabWidget()
        
        # Add employee details tab
        self.details_tab = EmployeeDetailsTab(self.db, self.emp_db.db_path)
        self.details_tab.employees_changed.connect(self.employees_changed.emit)  # Forward the signal
        tabs.addTab(self.details_tab, "بيانات الموظفين")
        
        # Add employee status tab
        self.status_tab = EmployeeStatusTab(self.emp_db)
        tabs.addTab(self.status_tab, "حالات الموظفين")
        
        # Add employee shifts tab
        self.shifts_tab = EmployeeShiftsTab(self.emp_db)
        tabs.addTab(self.shifts_tab, "الورديات")
        
        layout.addWidget(tabs)
        
    def connect_to_departments_tab(self, departments_tab):
        """Connect to departments tab signals"""
        departments_tab.departments_changed.connect(self.details_tab.update_combos) 