from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
                               QMessageBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from ...database.departments_db import DepartmentsDatabase
from ...database.employees_db import EmployeesDatabase
from ...database.database import Database

class EmployeeStatusTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.emp_db = EmployeesDatabase(self.db.db_path)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Employee selection
        emp_layout = QHBoxLayout()
        emp_label = QLabel("الموظف:")
        self.emp_combo = QComboBox()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        emp_layout.addWidget(self.emp_combo)
        emp_layout.addWidget(emp_label)
        
        # Status type selection
        status_layout = QHBoxLayout()
        status_label = QLabel("نوع الحالة:")
        self.status_combo = QComboBox()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        status_layout.addWidget(self.status_combo)
        status_layout.addWidget(status_label)
        
        # Date selection
        dates_layout = QHBoxLayout()
        
        # Start date
        start_date_layout = QHBoxLayout()
        start_date_label = QLabel("تاريخ البداية:")
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        start_date_layout.addWidget(self.start_date)
        start_date_layout.addWidget(start_date_label)
        
        # End date
        end_date_layout = QHBoxLayout()
        end_date_label = QLabel("تاريخ النهاية:")
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        end_date_layout.addWidget(self.end_date)
        end_date_layout.addWidget(end_date_label)
        
        dates_layout.addLayout(end_date_layout)
        dates_layout.addLayout(start_date_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("إضافة حالة")
        self.approve_btn = QPushButton("الموافقة على الحالة")
        buttons_layout.addWidget(self.approve_btn)
        buttons_layout.addWidget(self.add_btn)
        
        # Status table
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(7)
        self.status_table.setHorizontalHeaderLabels([
            "حالة الموافقة",
            "تاريخ الموافقة",
            "تاريخ النهاية",
            "تاريخ البداية",
            "نوع الحالة",
            "اسم الموظف",
            "رقم الموظف"
        ])
        
        # Add all layouts
        layout.addLayout(emp_layout)
        layout.addLayout(status_layout)
        layout.addLayout(dates_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.status_table)
        
        # Connect signals
        self.add_btn.clicked.connect(self.handle_add)
        self.approve_btn.clicked.connect(self.handle_approve)
        self.status_table.itemClicked.connect(self.handle_table_click)
        self.emp_combo.currentIndexChanged.connect(self.update_status_table)
        
        # Initial updates
        self.update_combos()
        self.update_status_table()
        
    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])

    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])

    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])

    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
        
    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
        
    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
        
    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
        
    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
        
    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', ""))))

    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
        
    def update_combos(self):
        """Update employee and status type combo boxes."""
        # Update employees combo
        current_emp = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("-- اختر الموظف --", None)
        employees = self.emp_db.get_all_employees()
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.emp_combo.addItem(f"{emp['name']} ({department})", emp['id'])
            
        # Restore previous selection if it still exists
        if current_emp:
            index = self.emp_combo.findData(current_emp)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
                
        # Update status types combo
        if hasattr(self.db, 'get_status_types'):
            status_types = self.db.get_status_types()
        else:
            status_types = DepartmentsDatabase(self.db.db_path).get_status_types()
        current_status = self.status_combo.currentData()
        self.status_combo.clear()
        self.status_combo.addItem("-- اختر نوع الحالة --", None)
        for status in status_types:
            self.status_combo.addItem(status['name'], status['id'])
            
        # Restore previous selection if it still exists
        if current_status:
            index = self.status_combo.findData(current_status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
    def handle_add(self):
        """Add a new status record for the selected employee."""
        employee_id = self.emp_combo.currentData()
        status_type_id = self.status_combo.currentData()
        start_date = self.start_date.date().toString(Qt.DateFormat.ISODate)
        end_date = self.end_date.date().toString(Qt.DateFormat.ISODate)
        
        # Validate inputs
        if not employee_id or not status_type_id:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار الموظف ونوع الحالة")
            return
            
        if self.start_date.date() > self.end_date.date():
            QMessageBox.warning(self, "تنبيه", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
            
        # Try to add status
        if self.db.add_employee_status(employee_id, status_type_id, start_date, end_date):
            self.clear_inputs()
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تم إضافة الحالة بنجاح")
        else:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء إضافة الحالة")
            
    def handle_approve(self):
        """Approve the selected status record."""
        selected_items = self.status_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يجب اختيار حالة للموافقة عليها")
            return
            
        row = selected_items[0].row()
        
        # Get the status approval state
        approval_item = self.status_table.item(row, 0)
        if not approval_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        if approval_item.text() == "تمت الموافقة":
            QMessageBox.information(self, "تنبيه", "هذه الحالة تمت الموافقة عليها مسبقاً")
            return
            
        # Get required data
        emp_id_item = self.status_table.item(row, 6)
        start_date_item = self.status_table.item(row, 3)
        
        if not emp_id_item or not start_date_item:
            QMessageBox.warning(self, "خطأ", "بيانات الحالة غير مكتملة")
            return
            
        employee_id = emp_id_item.text()
        start_date = start_date_item.text()
        
        # Get the status ID
        status_id = self.db.get_status_id(employee_id, start_date)
        if not status_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على الحالة المحددة")
            return
            
        # Try to approve status
        if self.db.approve_employee_status(status_id=status_id, approved_by=employee_id):
            self.update_status_table()
            QMessageBox.information(self, "نجاح", "تمت الموافقة على الحالة بنجاح")
        else:
            QMessageBox.warning(
                self, 
                "خطأ", 
                "حدث خطأ أثناء الموافقة على الحالة.\n"
                "تأكد من أن لديك صلاحية الموافقة على الحالات."
            )
            
    def handle_table_click(self, item):
        """Handle clicking on a status record in the table."""
        row = item.row()
        
        # Find and set employee in combo
        emp_id_item = self.status_table.item(row, 6)
        if emp_id_item:
            emp_id = emp_id_item.text()
            index = self.emp_combo.findData(emp_id)
            if index >= 0:
                self.emp_combo.setCurrentIndex(index)
            
        # Find and set status type in combo
        status_item = self.status_table.item(row, 4)
        if status_item:
            status_name = status_item.text()
            for i in range(self.status_combo.count()):
                if self.status_combo.itemText(i) == status_name:
                    self.status_combo.setCurrentIndex(i)
                    break
                
        # Set dates
        start_date_item = self.status_table.item(row, 3)
        end_date_item = self.status_table.item(row, 2)
        
        if start_date_item and start_date_item.text():
            start_date = QDate.fromString(
                start_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if start_date.isValid():
                self.start_date.setDate(start_date)
                
        if end_date_item and end_date_item.text():
            end_date = QDate.fromString(
                end_date_item.text(),
                Qt.DateFormat.ISODate
            )
            if end_date.isValid():
                self.end_date.setDate(end_date)
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.emp_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
    def update_status_table(self):
        """Update the status table with current data."""
        employee_id = self.emp_combo.currentData()
        
        if employee_id:
            # Get status history for specific employee
            status_records = self.db.get_employee_status(employee_id)
        else:
            # Get all status records from all departments
            all_records = []
            departments = self.db.get_all_departments()
            for dept in departments:
                dept_records = self.db.get_department_status(dept['code'])
                all_records.extend(dept_records)
            status_records = all_records
            
        self.status_table.setRowCount(len(status_records))
        
        for row, record in enumerate(status_records):
            # Convert approval status to text
            approval_status = "تمت الموافقة" if record.get('approved', True) else "في انتظار الموافقة"
            approval_date = record.get('approval_date', "")
            
            self.status_table.setItem(row, 0, QTableWidgetItem(approval_status))
            self.status_table.setItem(row, 1, QTableWidgetItem(str(approval_date)))
            self.status_table.setItem(row, 2, QTableWidgetItem(record.get('end_date', "")))
            self.status_table.setItem(row, 3, QTableWidgetItem(record.get('start_date', "")))
            self.status_table.setItem(row, 4, QTableWidgetItem(record.get('status_type', "")))
            self.status_table.setItem(row, 5, QTableWidgetItem(record.get('employee_name', "")))
            self.status_table.setItem(row, 6, QTableWidgetItem(str(record.get('employee_id', "")))) 