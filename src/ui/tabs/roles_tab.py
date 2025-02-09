from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from ...database.departments_db import DepartmentsDatabase

class RolesTab(QWidget):
    def __init__(self, db: DepartmentsDatabase):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the roles management UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Role management group
        role_group = QGroupBox("إدارة الأدوار الوظيفية")
        role_group.setStyleSheet("""
            QGroupBox {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 15px;
                font-size: 14px;
            }
            QGroupBox::title {
                color: #495057;
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)
        role_layout = QVBoxLayout(role_group)
        role_layout.setContentsMargins(15, 15, 15, 15)
        role_layout.setSpacing(10)
        
        # Role input
        input_layout = QHBoxLayout()
        name_label = QLabel("اسم الدور الوظيفي:")
        name_label.setStyleSheet("font-weight: bold; color: #495057;")
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4dabf7;
            }
        """)
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(name_label)
        role_layout.addLayout(input_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("إضافة")
        self.update_btn = QPushButton("تحديث")
        self.delete_btn = QPushButton("حذف")
        
        button_style = """
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        """
        
        self.add_btn.setStyleSheet(button_style + "background-color: #40c057;")
        self.update_btn.setStyleSheet(button_style + "background-color: #228be6;")
        self.delete_btn.setStyleSheet(button_style + "background-color: #fa5252;")
        
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addStretch()
        role_layout.addLayout(buttons_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-right: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            QTableWidget::item:selected {
                background-color: #e7f5ff;
                color: #1864ab;
            }
        """)
        self.table.setColumnCount(2)
        headers = ["عدد الموظفين", "اسم الدور"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setStretchLastSection(True)
        role_layout.addWidget(self.table)
        
        layout.addWidget(role_group)
        
        # Connect signals
        self.add_btn.clicked.connect(self.handle_add)
        self.update_btn.clicked.connect(self.handle_update)
        self.delete_btn.clicked.connect(self.handle_delete)
        self.table.clicked.connect(self.handle_selection)
        
        # Initial data load
        self.refresh_table()
        
    def refresh_table(self):
        """Refresh roles table"""
        roles = self.db.get_all_roles()
        self.table.setRowCount(len(roles))
        
        for i, role in enumerate(roles):
            items = [
                QTableWidgetItem(str(role['employee_count'])),
                QTableWidgetItem(role['name'])
            ]
            
            for j, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)
                
        self.table.resizeColumnsToContents()
        
    def clear_inputs(self):
        """Clear all input fields"""
        self.name_input.clear()
        self.update_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
    def handle_selection(self):
        """Handle role selection from table"""
        row = self.table.currentRow()
        if row >= 0:
            role_name = self.table.item(row, 1).text()
            self.name_input.setText(role_name)
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            
    def handle_add(self):
        """Handle adding a new role"""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(
                self,
                "خطأ",
                "الرجاء إدخال اسم الدور الوظيفي"
            )
            return
            
        if self.db.add_role(name):
            self.refresh_table()
            self.clear_inputs()
            QMessageBox.information(
                self,
                "نجاح",
                "تم إضافة الدور الوظيفي بنجاح"
            )
        else:
            QMessageBox.warning(
                self,
                "خطأ",
                "فشل إضافة الدور الوظيفي. قد يكون الاسم مستخدماً بالفعل"
            )
            
    def handle_update(self):
        """Handle updating a role"""
        old_name = self.table.item(self.table.currentRow(), 1).text()
        new_name = self.name_input.text().strip()
        
        if not new_name:
            QMessageBox.warning(
                self,
                "خطأ",
                "الرجاء إدخال اسم الدور الوظيفي"
            )
            return
            
        if self.db.update_role(old_name, new_name):
            self.refresh_table()
            self.clear_inputs()
            QMessageBox.information(
                self,
                "نجاح",
                "تم تحديث الدور الوظيفي بنجاح"
            )
        else:
            QMessageBox.warning(
                self,
                "خطأ",
                "فشل تحديث الدور الوظيفي"
            )
            
    def handle_delete(self):
        """Handle deleting a role"""
        name = self.name_input.text().strip()
        
        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الدور الوظيفي؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_role(name):
                self.refresh_table()
                self.clear_inputs()
                QMessageBox.information(
                    self,
                    "نجاح",
                    "تم حذف الدور الوظيفي بنجاح"
                )
            else:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    "لا يمكن حذف الدور الوظيفي لأنه مستخدم من قبل موظفين"
                ) 