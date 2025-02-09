from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                               QMessageBox, QSpinBox, QCheckBox)
from PyQt6.QtCore import Qt
from ...database.departments_db import DepartmentsDatabase

class StatusTypesTab(QWidget):
    def __init__(self, db: DepartmentsDatabase, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Input fields
        input_layout = QHBoxLayout()
        
        # Status name
        name_layout = QHBoxLayout()
        name_label = QLabel("نوع الإجازة:")
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        name_layout.addWidget(name_label)
        
        # Max days
        days_layout = QHBoxLayout()
        days_label = QLabel("الحد الأقصى للأيام:")
        self.days_input = QSpinBox()
        self.days_input.setMinimum(0)
        self.days_input.setMaximum(365)
        days_layout.addWidget(self.days_input)
        days_layout.addWidget(days_label)
        
        # Requires approval
        approval_layout = QHBoxLayout()
        approval_label = QLabel("تتطلب موافقة:")
        self.approval_check = QCheckBox()
        self.approval_check.setChecked(True)
        approval_layout.addWidget(self.approval_check)
        approval_layout.addWidget(approval_label)
        
        input_layout.addLayout(approval_layout)
        input_layout.addLayout(days_layout)
        input_layout.addLayout(name_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("إضافة")
        self.update_btn = QPushButton("تحديث")
        self.delete_btn = QPushButton("حذف")
        
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addStretch()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        headers = [
            "عدد الموظفين",
            "تتطلب موافقة",
            "الحد الأقصى للأيام",
            "نوع الإجازة"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Add all layouts
        layout.addLayout(input_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # Connect signals
        self.add_btn.clicked.connect(self.handle_add)
        self.update_btn.clicked.connect(self.handle_update)
        self.delete_btn.clicked.connect(self.handle_delete)
        self.table.clicked.connect(self.handle_selection)
        
        # Initial data load
        self.refresh_table()
        
    def refresh_table(self):
        """Refresh status types table."""
        types = self.db.get_all_status_types()
        self.table.setRowCount(len(types))
        
        for i, status_type in enumerate(types):
            items = [
                QTableWidgetItem(str(status_type['employee_count'])),
                QTableWidgetItem("نعم" if status_type['requires_approval'] else "لا"),
                QTableWidgetItem(str(status_type['max_days'] or "غير محدد")),
                QTableWidgetItem(status_type['name'])
            ]
            
            for j, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)
                
        self.table.resizeColumnsToContents()
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.name_input.clear()
        self.days_input.setValue(0)
        self.approval_check.setChecked(True)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
    def handle_selection(self):
        """Handle status type selection from table."""
        row = self.table.currentRow()
        if row >= 0:
            self.name_input.setText(self.table.item(row, 3).text())
            
            # Set max days
            max_days_text = self.table.item(row, 2).text()
            self.days_input.setValue(
                int(max_days_text) if max_days_text != "غير محدد" else 0
            )
            
            # Set requires approval
            self.approval_check.setChecked(
                self.table.item(row, 1).text() == "نعم"
            )
            
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            
    def handle_add(self):
        """Handle adding a new status type."""
        name = self.name_input.text().strip()
        max_days = self.days_input.value() or None
        requires_approval = self.approval_check.isChecked()
        
        if not name:
            QMessageBox.warning(
                self,
                "خطأ",
                "الرجاء إدخال نوع الإجازة"
            )
            return
            
        if self.db.add_status_type(name, requires_approval, max_days):
            self.refresh_table()
            self.clear_inputs()
            QMessageBox.information(
                self,
                "نجاح",
                "تم إضافة نوع الإجازة بنجاح"
            )
        else:
            QMessageBox.warning(
                self,
                "خطأ",
                "فشل إضافة نوع الإجازة. قد يكون الاسم مستخدماً بالفعل"
            )
            
    def handle_update(self):
        """Handle updating a status type."""
        old_name = self.table.item(self.table.currentRow(), 3).text()
        new_name = self.name_input.text().strip()
        max_days = self.days_input.value() or None
        requires_approval = self.approval_check.isChecked()
        
        if not new_name:
            QMessageBox.warning(
                self,
                "خطأ",
                "الرجاء إدخال نوع الإجازة"
            )
            return
            
        if self.db.update_status_type(old_name, new_name, requires_approval, max_days):
            self.refresh_table()
            self.clear_inputs()
            QMessageBox.information(
                self,
                "نجاح",
                "تم تحديث نوع الإجازة بنجاح"
            )
        else:
            QMessageBox.warning(
                self,
                "خطأ",
                "فشل تحديث نوع الإجازة"
            )
            
    def handle_delete(self):
        """Handle deleting a status type."""
        name = self.name_input.text().strip()
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف نوع الإجازة هذا؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_status_type(name):
                self.refresh_table()
                self.clear_inputs()
                QMessageBox.information(
                    self,
                    "نجاح",
                    "تم حذف نوع الإجازة بنجاح"
                )
            else:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    "لا يمكن حذف نوع الإجازة لأنه مستخدم من قبل موظفين"
                )

    def load_status_types(self):
        """تحميل أنواع الحالات من قاعدة البيانات"""
        self.status_types = self.db.get_all_status_types()
        self.update_table()
        
    def update_table(self):
        """تحديث الجدول بالبيانات الجديدة"""
        self.table.setRowCount(len(self.status_types))
        for row, status in enumerate(self.status_types):
            # عرض عدد الموظفين
            self.table.setItem(row, 0, QTableWidgetItem(str(status['employee_count'])))
            # عرض إذا كان يتطلب موافقة
            approval_text = "نعم" if status['requires_approval'] else "لا"
            self.table.setItem(row, 1, QTableWidgetItem(approval_text))
            # عرض الحد الأقصى للأيام
            max_days_text = str(status['max_days']) if status['max_days'] is not None else "غير محدد"
            self.table.setItem(row, 2, QTableWidgetItem(max_days_text))
            # عرض نوع الإجازة (الاسم)
            self.table.setItem(row, 3, QTableWidgetItem(status['name'])) 