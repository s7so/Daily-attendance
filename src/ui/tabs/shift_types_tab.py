from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                               QMessageBox, QSpinBox, QCheckBox, QTimeEdit)
from PyQt6.QtCore import Qt, QTime
from ...database.departments_db import DepartmentsDatabase

class ShiftTypesTab(QWidget):
    def __init__(self, db: DepartmentsDatabase, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Input fields
        input_layout = QHBoxLayout()
        
        # Shift name
        name_layout = QHBoxLayout()
        name_label = QLabel("اسم الوردية:")
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        name_layout.addWidget(name_label)
        
        # Start time
        start_layout = QHBoxLayout()
        start_label = QLabel("وقت البداية:")
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm")
        start_layout.addWidget(self.start_time)
        start_layout.addWidget(start_label)
        
        # End time
        end_layout = QHBoxLayout()
        end_label = QLabel("وقت النهاية:")
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm")
        end_layout.addWidget(self.end_time)
        end_layout.addWidget(end_label)
        
        # Break duration
        break_layout = QHBoxLayout()
        break_label = QLabel("مدة الاستراحة (دقيقة):")
        self.break_input = QSpinBox()
        self.break_input.setMinimum(0)
        self.break_input.setMaximum(120)
        self.break_input.setValue(60)
        break_layout.addWidget(self.break_input)
        break_layout.addWidget(break_label)
        
        # Flexible minutes
        flex_layout = QHBoxLayout()
        flex_label = QLabel("مرونة الحضور (دقيقة):")
        self.flex_input = QSpinBox()
        self.flex_input.setMinimum(0)
        self.flex_input.setMaximum(60)
        flex_layout.addWidget(self.flex_input)
        flex_layout.addWidget(flex_label)
        
        # Overtime allowed
        overtime_layout = QHBoxLayout()
        overtime_label = QLabel("يسمح بالعمل الإضافي:")
        self.overtime_check = QCheckBox()
        overtime_layout.addWidget(self.overtime_check)
        overtime_layout.addWidget(overtime_label)
        
        input_layout.addLayout(overtime_layout)
        input_layout.addLayout(flex_layout)
        input_layout.addLayout(break_layout)
        input_layout.addLayout(end_layout)
        input_layout.addLayout(start_layout)
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
        self.table.setColumnCount(7)
        headers = [
            "عدد الموظفين",
            "عمل إضافي",
            "مرونة (دقيقة)",
            "استراحة (دقيقة)",
            "وقت النهاية",
            "وقت البداية",
            "اسم الوردية"
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
        """تحديث جدول أنواع الورديات"""
        self.shift_types = self.db.get_all_shift_types()
        self.table.setRowCount(len(self.shift_types))
        
        for row, shift in enumerate(self.shift_types):
            # عدد الموظفين
            self.table.setItem(row, 0, QTableWidgetItem(str(shift['employee_count'])))
            # عمل إضافي
            self.table.setItem(row, 1, QTableWidgetItem("نعم" if shift['overtime_allowed'] else "لا"))
            # مرونة (دقيقة)
            self.table.setItem(row, 2, QTableWidgetItem(str(shift['flexible_minutes'])))
            # استراحة (دقيقة)
            self.table.setItem(row, 3, QTableWidgetItem(str(shift['break_duration'])))
            # وقت النهاية
            self.table.setItem(row, 4, QTableWidgetItem(shift['end_time']))
            # وقت البداية
            self.table.setItem(row, 5, QTableWidgetItem(shift['start_time']))
            # اسم الوردية
            self.table.setItem(row, 6, QTableWidgetItem(shift['name']))
        
        self.table.resizeColumnsToContents()
        
    def clear_inputs(self):
        """Clear all input fields."""
        self.name_input.clear()
        self.start_time.setTime(QTime(8, 0))  # 8:00 AM default
        self.end_time.setTime(QTime(16, 0))   # 4:00 PM default
        self.break_input.setValue(60)
        self.flex_input.setValue(0)
        self.overtime_check.setChecked(False)
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
    def handle_selection(self):
        """Handle shift type selection from table."""
        row = self.table.currentRow()
        if row >= 0:
            self.name_input.setText(self.table.item(row, 6).text())
            
            # Set times
            start_time = QTime.fromString(self.table.item(row, 5).text(), "HH:mm")
            end_time = QTime.fromString(self.table.item(row, 4).text(), "HH:mm")
            self.start_time.setTime(start_time)
            self.end_time.setTime(end_time)
            
            # Set break duration
            self.break_input.setValue(int(self.table.item(row, 3).text()))
            
            # Set flexible minutes
            self.flex_input.setValue(int(self.table.item(row, 2).text()))
            
            # Set overtime allowed
            self.overtime_check.setChecked(
                self.table.item(row, 1).text() == "نعم"
            )
            
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            
    def handle_add(self):
        """Handle adding a new shift type."""
        name = self.name_input.text().strip()
        start_time = self.start_time.time().toString("HH:mm")
        end_time = self.end_time.time().toString("HH:mm")
        break_duration = self.break_input.value()
        flexible_minutes = self.flex_input.value()
        overtime_allowed = self.overtime_check.isChecked()
        
        if not name:
            QMessageBox.warning(
                self,
                "خطأ",
                "الرجاء إدخال اسم الوردية"
            )
            return
            
        if self.db.add_shift_type(
            name, start_time, end_time, break_duration,
            flexible_minutes, overtime_allowed
        ):
            self.refresh_table()
            self.clear_inputs()
            QMessageBox.information(
                self,
                "نجاح",
                "تم إضافة الوردية بنجاح"
            )
        else:
            QMessageBox.warning(
                self,
                "خطأ",
                "فشل إضافة الوردية. قد يكون الاسم مستخدماً بالفعل"
            )
            
    def handle_update(self):
        """Handle updating a shift type."""
        old_name = self.table.item(self.table.currentRow(), 6).text()
        new_name = self.name_input.text().strip()
        start_time = self.start_time.time().toString("HH:mm")
        end_time = self.end_time.time().toString("HH:mm")
        break_duration = self.break_input.value()
        flexible_minutes = self.flex_input.value()
        overtime_allowed = self.overtime_check.isChecked()
        
        if not new_name:
            QMessageBox.warning(
                self,
                "خطأ",
                "الرجاء إدخال اسم الوردية"
            )
            return
            
        if self.db.update_shift_type(
            old_name, new_name, start_time, end_time,
            break_duration, flexible_minutes, overtime_allowed
        ):
            self.refresh_table()
            self.clear_inputs()
            QMessageBox.information(
                self,
                "نجاح",
                "تم تحديث الوردية بنجاح"
            )
        else:
            QMessageBox.warning(
                self,
                "خطأ",
                "فشل تحديث الوردية"
            )
            
    def handle_delete(self):
        """Handle deleting a shift type."""
        name = self.name_input.text().strip()
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذه الوردية؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_shift_type(name):
                self.refresh_table()
                self.clear_inputs()
                QMessageBox.information(
                    self,
                    "نجاح",
                    "تم حذف الوردية بنجاح"
                )
            else:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    "لا يمكن حذف الوردية لأنها مستخدمة من قبل موظفين"
                ) 