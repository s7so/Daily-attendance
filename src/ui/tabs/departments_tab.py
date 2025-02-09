from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QMessageBox, QComboBox,
                               QTabWidget, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from ...database.departments_db import DepartmentsDatabase

class TransferHistoryDialog(QDialog):
    def __init__(self, db: DepartmentsDatabase, employee_id: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.employee_id = employee_id
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("سجل نقل الموظف")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(
            ["التاريخ", "القسم السابق", "القسم الجديد"]
        )
        
        layout.addWidget(self.history_table)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Load history
        self.load_history()
        
    def load_history(self):
        history = self.db.get_employee_department_history(self.employee_id)
        self.history_table.setRowCount(len(history))
        
        for row, record in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(record['date']))
            self.history_table.setItem(row, 1, QTableWidgetItem(record['old_department']))
            self.history_table.setItem(row, 2, QTableWidgetItem(record['new_department']))

class DepartmentsTab(QWidget):
    departments_changed = pyqtSignal()  # Signal to notify when departments list changes
    
    def __init__(self, db: DepartmentsDatabase):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Department details input
        form_layout = QVBoxLayout()
        
        # Code input
        code_layout = QHBoxLayout()
        code_label = QLabel("رمز القسم:")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("أدخل رمز القسم (مثال: HR, IT)")
        code_layout.addWidget(self.code_input)
        code_layout.addWidget(code_label)
        
        # Name input
        name_layout = QHBoxLayout()
        name_label = QLabel("اسم القسم:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("أدخل اسم القسم")
        name_layout.addWidget(self.name_input)
        name_layout.addWidget(name_label)
        
        # Manager selection
        manager_layout = QHBoxLayout()
        manager_label = QLabel("مدير القسم:")
        self.manager_combo = QComboBox()
        self.manager_combo.addItem("-- اختر مدير القسم --", None)
        manager_layout.addWidget(self.manager_combo)
        manager_layout.addWidget(manager_label)
        
        # Department management buttons
        dept_buttons_layout = QHBoxLayout()
        self.add_dept_btn = QPushButton("إضافة قسم")
        self.update_dept_btn = QPushButton("تحديث القسم")
        self.delete_dept_btn = QPushButton("حذف القسم")
        dept_buttons_layout.addWidget(self.delete_dept_btn)
        dept_buttons_layout.addWidget(self.update_dept_btn)
        dept_buttons_layout.addWidget(self.add_dept_btn)
        
        # Departments table
        self.departments_table = QTableWidget()
        self.departments_table.setColumnCount(4)
        self.departments_table.setHorizontalHeaderLabels(
            ["مدير القسم", "اسم القسم", "رمز القسم", "عدد الموظفين"]
        )
        
        # Employee transfer section
        transfer_layout = QHBoxLayout()
        self.employee_combo = QComboBox()
        self.employee_combo.addItem("-- اختر الموظف --", None)
        self.dept_combo = QComboBox()
        self.dept_combo.addItem("-- اختر القسم الجديد --", None)
        self.transfer_btn = QPushButton("نقل الموظف")
        self.history_btn = QPushButton("سجل النقل")
        
        transfer_layout.addWidget(self.history_btn)
        transfer_layout.addWidget(self.transfer_btn)
        transfer_layout.addWidget(self.dept_combo)
        transfer_layout.addWidget(QLabel("إلى القسم:"))
        transfer_layout.addWidget(self.employee_combo)
        transfer_layout.addWidget(QLabel("نقل الموظف:"))
        
        # Add all layouts
        form_layout.addLayout(code_layout)
        form_layout.addLayout(name_layout)
        form_layout.addLayout(manager_layout)
        
        layout.addLayout(form_layout)
        layout.addLayout(dept_buttons_layout)
        layout.addWidget(self.departments_table)
        layout.addLayout(transfer_layout)
        
        # Connect signals
        self.add_dept_btn.clicked.connect(self.handle_add_department)
        self.update_dept_btn.clicked.connect(self.handle_update_department)
        self.delete_dept_btn.clicked.connect(self.handle_delete_department)
        self.departments_table.itemClicked.connect(self.handle_table_click)
        self.transfer_btn.clicked.connect(self.handle_transfer)
        self.history_btn.clicked.connect(self.show_transfer_history)
        
        # Initial updates
        self.update_departments_table()
        self.update_combos()
        
    def update_combos(self):
        """Update all combo boxes with fresh data."""
        # Update manager combo
        current_manager = self.manager_combo.currentData()  # Save current selection
        self.manager_combo.clear()
        self.manager_combo.addItem("-- اختر مدير القسم --", None)
        
        # Get all managers
        managers = self.db.get_managers()
        for manager in managers:
            department = manager.get('department_name') or manager.get('department', '')
            self.manager_combo.addItem(
                f"{manager['name']} ({department})", 
                manager['id']
            )
            
        # Restore previous selection if it still exists
        if current_manager:
            index = self.manager_combo.findData(current_manager)
            if index >= 0:
                self.manager_combo.setCurrentIndex(index)
            
        # Update employee combo for transfer
        current_employee = self.employee_combo.currentData()  # Save current selection
        self.employee_combo.clear()
        self.employee_combo.addItem("-- اختر الموظف --", None)
        
        # Get all employees
        employees = self.db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.employee_combo.addItem(
                f"{emp['name']} ({department})", 
                emp['id']
            )
            
        # Restore previous selection if it still exists
        if current_employee:
            index = self.employee_combo.findData(current_employee)
            if index >= 0:
                self.employee_combo.setCurrentIndex(index)
            
        # Update department combo for transfer
        current_dept = self.dept_combo.currentData()  # Save current selection
        self.dept_combo.clear()
        self.dept_combo.addItem("-- اختر القسم الجديد --", None)
        
        # Get all departments
        departments = self.db.get_all_departments()
        for dept in departments:
            self.dept_combo.addItem(dept['name'], dept['code'])
            
        # Restore previous selection if it still exists
        if current_dept:
            index = self.dept_combo.findData(current_dept)
            if index >= 0:
                self.dept_combo.setCurrentIndex(index)
                
    def handle_add_department(self):
        code = self.code_input.text().strip().upper()
        name = self.name_input.text().strip()
        manager_id = self.manager_combo.currentData()
        
        if not code or not name:
            QMessageBox.warning(self, "تنبيه", "يجب إدخال رمز واسم القسم")
            return
            
        if self.db.add_department(code, name, manager_id):
            self.clear_inputs()
            self.update_departments_table()
            self.update_combos()
            self.departments_changed.emit()  # Emit signal when department is added
            QMessageBox.information(self, "نجاح", "تم إضافة القسم بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "رمز القسم موجود بالفعل")
            
    def handle_update_department(self):
        code = self.code_input.text().strip().upper()
        name = self.name_input.text().strip()
        manager_id = self.manager_combo.currentData()
        
        if not code or not name:
            QMessageBox.warning(self, "تنبيه", "يجب إدخال رمز واسم القسم")
            return
            
        if self.db.update_department(code, name, manager_id):
            self.clear_inputs()
            self.update_departments_table()
            self.update_combos()
            self.departments_changed.emit()  # Emit signal when department is updated
            QMessageBox.information(self, "نجاح", "تم تحديث القسم بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على القسم")
            
    def handle_delete_department(self):
        code = self.code_input.text().strip().upper()
        
        if not code:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار القسم أولاً")
            return
            
        reply = QMessageBox.question(
            self, 
            "تأكيد",
            "هل أنت متأكد من حذف هذا القسم؟\n"
            "لا يمكن حذف قسم به موظفين.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_department(code):
                self.clear_inputs()
                self.update_departments_table()
                self.update_combos()
                self.departments_changed.emit()  # Emit signal when department is deleted
                QMessageBox.information(self, "نجاح", "تم حذف القسم بنجاح")
            else:
                QMessageBox.warning(
                    self, 
                    "خطأ", 
                    "لا يمكن حذف القسم.\n"
                    "تأكد من أن القسم موجود وليس به موظفين."
                )
                
    def handle_transfer(self):
        employee_id = self.employee_combo.currentData()
        new_dept_code = self.dept_combo.currentData()
        
        if not employee_id or not new_dept_code:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف والقسم الجديد")
            return
            
        if self.db.transfer_employee(employee_id, new_dept_code):
            self.update_departments_table()
            self.update_combos()
            QMessageBox.information(
                self, 
                "نجاح", 
                f"تم نقل الموظف إلى {self.dept_combo.currentText()} بنجاح"
            )
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء نقل الموظف")
            
    def show_transfer_history(self):
        employee_id = self.employee_combo.currentData()
        
        if not employee_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف أولاً")
            return
            
        dialog = TransferHistoryDialog(self.db, employee_id, self)
        dialog.exec()
        
    def handle_table_click(self, item):
        row = item.row()
        self.code_input.setText(self.departments_table.item(row, 2).text())
        self.name_input.setText(self.departments_table.item(row, 1).text())
        
        # Find and set the manager in combo
        manager_name = self.departments_table.item(row, 0).text()
        if manager_name != "لا يوجد":
            for i in range(self.manager_combo.count()):
                if manager_name in self.manager_combo.itemText(i):
                    self.manager_combo.setCurrentIndex(i)
                    break
        else:
            self.manager_combo.setCurrentIndex(0)
        
    def clear_inputs(self):
        self.code_input.clear()
        self.name_input.clear()
        self.manager_combo.setCurrentIndex(0)
        
    def update_departments_table(self):
        """Update departments table with fresh data."""
        departments = self.db.get_all_departments()
        self.departments_table.setRowCount(len(departments))
        
        for row, dept in enumerate(departments):
            # Get manager name from the managers list
            manager_name = "لا يوجد"
            if dept.get('manager_id'):
                managers = self.db.get_managers()
                for manager in managers:
                    if manager['id'] == dept['manager_id']:
                        manager_name = manager['name']
                        break

            self.departments_table.setItem(row, 0, QTableWidgetItem(manager_name))
            self.departments_table.setItem(row, 1, QTableWidgetItem(dept['name']))
            self.departments_table.setItem(row, 2, QTableWidgetItem(dept['code']))
            
            # Get employee count
            employees = self.db.get_department_employees(dept['code'])
            self.departments_table.setItem(row, 3, QTableWidgetItem(str(len(employees)))) 