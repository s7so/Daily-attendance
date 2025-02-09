from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QTextEdit, QMessageBox,
    QSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ..styles import (
    BUTTON_STYLE, TABLE_STYLE, INPUT_STYLE,
    LABEL_STYLE, GROUP_BOX_STYLE,
    FONT_CONFIG, LAYOUT_SPACING, WIDGET_MARGINS
)
from ...database.departments_db import DepartmentsDatabase

class LeavesTab(QWidget):
    def __init__(self, db: DepartmentsDatabase):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(LAYOUT_SPACING)
        layout.setContentsMargins(WIDGET_MARGINS, WIDGET_MARGINS, WIDGET_MARGINS, WIDGET_MARGINS)
        
        # Create leave request group
        request_group = QGroupBox("طلب إجازة جديد")
        request_group.setStyleSheet(GROUP_BOX_STYLE)
        request_layout = QVBoxLayout(request_group)
        
        # Create form layout for inputs
        form_layout = QHBoxLayout()
        form_layout.setSpacing(LAYOUT_SPACING)
        
        # Employee selection
        employee_layout = QVBoxLayout()
        employee_label = QLabel("الموظف:")
        employee_label.setStyleSheet(LABEL_STYLE)
        self.employee_combo = QComboBox()
        self.employee_combo.setStyleSheet(INPUT_STYLE)
        self.employee_combo.setMinimumWidth(200)
        employee_layout.addWidget(employee_label)
        employee_layout.addWidget(self.employee_combo)
        form_layout.addLayout(employee_layout)
        
        # Leave type selection
        leave_type_layout = QVBoxLayout()
        leave_type_label = QLabel("نوع الإجازة:")
        leave_type_label.setStyleSheet(LABEL_STYLE)
        self.leave_type_combo = QComboBox()
        self.leave_type_combo.setStyleSheet(INPUT_STYLE)
        leave_type_layout.addWidget(leave_type_label)
        leave_type_layout.addWidget(self.leave_type_combo)
        form_layout.addLayout(leave_type_layout)
        
        # Date selection
        dates_layout = QVBoxLayout()
        start_date_label = QLabel("تاريخ البداية:")
        start_date_label.setStyleSheet(LABEL_STYLE)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setStyleSheet(INPUT_STYLE)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        
        end_date_label = QLabel("تاريخ النهاية:")
        end_date_label.setStyleSheet(LABEL_STYLE)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setStyleSheet(INPUT_STYLE)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        
        dates_layout.addWidget(start_date_label)
        dates_layout.addWidget(self.start_date_edit)
        dates_layout.addWidget(end_date_label)
        dates_layout.addWidget(self.end_date_edit)
        form_layout.addLayout(dates_layout)
        
        # Notes input
        notes_layout = QVBoxLayout()
        notes_label = QLabel("ملاحظات:")
        notes_label.setStyleSheet(LABEL_STYLE)
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(INPUT_STYLE)
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self.notes_edit)
        form_layout.addLayout(notes_layout)
        
        # Submit button
        button_layout = QVBoxLayout()
        self.submit_button = QPushButton("تقديم الطلب")
        self.submit_button.setStyleSheet(BUTTON_STYLE)
        button_layout.addWidget(self.submit_button)
        button_layout.addStretch()
        form_layout.addLayout(button_layout)
        
        request_layout.addLayout(form_layout)
        layout.addWidget(request_group)
        
        # Create table for displaying leave records
        records_group = QGroupBox("سجل الإجازات")
        records_group.setStyleSheet(GROUP_BOX_STYLE)
        records_layout = QVBoxLayout(records_group)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Department filter
        dept_label = QLabel("القسم:")
        dept_label.setStyleSheet(LABEL_STYLE)
        self.dept_combo = QComboBox()
        self.dept_combo.setStyleSheet(INPUT_STYLE)
        self.dept_combo.addItem("الكل")
        filter_layout.addWidget(dept_label)
        filter_layout.addWidget(self.dept_combo)
        
        # Status filter
        status_label = QLabel("الحالة:")
        status_label.setStyleSheet(LABEL_STYLE)
        self.status_combo = QComboBox()
        self.status_combo.setStyleSheet(INPUT_STYLE)
        self.status_combo.addItems(["الكل", "معتمد", "في الانتظار", "مرفوض"])
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_combo)
        
        filter_layout.addStretch()
        records_layout.addLayout(filter_layout)
        
        # Leave records table
        self.table = QTableWidget()
        self.table.setStyleSheet(TABLE_STYLE)
        self.setup_table()
        records_layout.addWidget(self.table)
        
        layout.addWidget(records_group)
        
        # Connect signals
        self.submit_button.clicked.connect(self.submit_leave_request)
        self.dept_combo.currentTextChanged.connect(self.refresh_data)
        self.status_combo.currentTextChanged.connect(self.refresh_data)
        
        # Load initial data
        self.load_employees()
        self.load_leave_types()
        self.load_departments()
        self.refresh_data()
        
    def setup_table(self):
        """Setup the leave records table."""
        headers = [
            "الموظف", "القسم", "نوع الإجازة", "تاريخ البداية",
            "تاريخ النهاية", "عدد الأيام", "الحالة", "ملاحظات"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        
        # Set column widths
        self.table.setColumnWidth(0, 150)  # Employee name
        self.table.setColumnWidth(1, 120)  # Department
        self.table.setColumnWidth(2, 120)  # Leave type
        self.table.setColumnWidth(3, 100)  # Start date
        self.table.setColumnWidth(4, 100)  # End date
        self.table.setColumnWidth(5, 80)   # Days count
        self.table.setColumnWidth(6, 80)   # Status
        self.table.setColumnWidth(7, 200)  # Notes
        
    def load_employees(self):
        """Load employees into the combo box."""
        employees = self.db.get_all_employees()
        self.employee_combo.clear()
        self.employee_combo.addItem("-- اختر الموظف --", None)
        for employee in employees:
            department = employee.get('department_name') or employee.get('department', '')
            self.employee_combo.addItem(f"{employee['name']} ({department})", employee['id'])
            
    def load_leave_types(self):
        """Load leave types into the combo box."""
        leave_types = self.db.get_status_types()
        self.leave_type_combo.clear()
        for leave_type in leave_types:
            if leave_type['name'] != 'حضور':  # Skip attendance status
                self.leave_type_combo.addItem(leave_type['name'], leave_type['id'])
                
    def load_departments(self):
        """Load departments into the filter combo box."""
        departments = self.db.get_all_departments()
        self.dept_combo.clear()
        self.dept_combo.addItem("الكل")
        for dept in departments:
            self.dept_combo.addItem(dept['name'], dept['code'])
            
    def refresh_data(self):
        """Refresh the leave records table."""
        # Get filter values
        department = self.dept_combo.currentData()
        status_text = self.status_combo.currentText()
        
        # Convert status text to boolean
        status_map = {
            "الكل": None,
            "معتمد": True,
            "في الانتظار": False,
            "مرفوض": None  # TODO: Add rejected status in database
        }
        status = status_map.get(status_text)
        
        # Get records based on filters
        if department:
            records = self.db.get_department_status(department)
        else:
            records = self.db.get_all_status(approved=status)
            
        self.table.setRowCount(len(records))
        for i, record in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(record.get('employee_name', '')))
            self.table.setItem(i, 1, QTableWidgetItem(record.get('department', '')))
            self.table.setItem(i, 2, QTableWidgetItem(record.get('status_type', '')))
            self.table.setItem(i, 3, QTableWidgetItem(record.get('start_date', '')))
            self.table.setItem(i, 4, QTableWidgetItem(record.get('end_date', '') or ''))
            
            # Calculate days count
            start = QDate.fromString(record.get('start_date', ''), "yyyy-MM-dd")
            end = QDate.fromString(record.get('end_date', '') or record.get('start_date', ''), "yyyy-MM-dd")
            days = str(start.daysTo(end) + 1)
            self.table.setItem(i, 5, QTableWidgetItem(days))
            
            # Set status text
            status_text = "معتمد" if record.get('approved', False) else "في الانتظار"
            approved_by = record.get('approved_by', '')
            if approved_by:
                status_text += f" (بواسطة {approved_by})"
            self.table.setItem(i, 6, QTableWidgetItem(status_text))
            
            self.table.setItem(i, 7, QTableWidgetItem(record.get('notes', '') or ''))
            
            # Center align all items
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
    def submit_leave_request(self):
        """Submit a new leave request."""
        employee_id = self.employee_combo.currentData()
        status_type_id = self.leave_type_combo.currentData()
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        notes = self.notes_edit.toPlainText()
        
        if self.db.add_employee_status(
            employee_id=employee_id,
            status_type_id=status_type_id,
            start_date=start_date,
            end_date=end_date,
            notes=notes
        ):
            QMessageBox.information(self, "نجاح", "تم تقديم طلب الإجازة بنجاح")
            self.notes_edit.clear()
            self.refresh_data()
        else:
            QMessageBox.warning(self, "خطأ", "فشل تقديم طلب الإجازة") 