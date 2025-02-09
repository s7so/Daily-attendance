from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QMessageBox, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from ..styles import (
    BUTTON_STYLE, TABLE_STYLE, INPUT_STYLE,
    LABEL_STYLE, GROUP_BOX_STYLE,
    FONT_CONFIG, LAYOUT_SPACING, WIDGET_MARGINS
)
from ...database.departments_db import DepartmentsDatabase

class PermissionsTab(QWidget):
    def __init__(self, db: DepartmentsDatabase):
        super().__init__()
        self.db = db
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the permissions management UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Role permissions group
        role_group = QGroupBox("صلاحيات الأدوار")
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
        
        # Role selection
        role_select_layout = QHBoxLayout()
        role_label = QLabel("الدور:")
        role_label.setStyleSheet("font-weight: bold; color: #495057;")
        
        self.role_combo = QComboBox()
        self.role_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                min-width: 200px;
            }
            QComboBox:focus {
                border-color: #4dabf7;
            }
        """)
        
        role_select_layout.addWidget(role_label)
        role_select_layout.addWidget(self.role_combo)
        role_select_layout.addStretch()
        role_layout.addLayout(role_select_layout)
        
        # Add separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #dee2e6;")
        role_layout.addWidget(line)
        
        # Role permissions table
        self.role_table = QTableWidget()
        self.role_table.setStyleSheet("""
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
        self.setup_role_table()
        role_layout.addWidget(self.role_table)
        
        layout.addWidget(role_group)
        
        # Connect signals
        self.role_combo.currentIndexChanged.connect(self.refresh_role_permissions)
        
        # Load initial data
        self.load_roles()
        
    def setup_role_table(self):
        """Setup the role permissions table"""
        headers = ["الصلاحية", "الوصف", "ممنوحة"]
        self.role_table.setColumnCount(len(headers))
        self.role_table.setHorizontalHeaderLabels(headers)
        self.role_table.setAlternatingRowColors(True)
        self.role_table.horizontalHeader().setStretchLastSection(True)
        self.role_table.verticalHeader().setVisible(False)
        
        # Set column widths
        self.role_table.setColumnWidth(0, 250)  # Permission name
        self.role_table.setColumnWidth(1, 400)  # Description
        self.role_table.setColumnWidth(2, 120)  # Granted
        
    def load_roles(self):
        """Load roles into the combo box"""
        roles = self.db.get_all_roles()
        self.role_combo.clear()
        for role in roles:
            self.role_combo.addItem(role['name'], role['id'])
            
    def refresh_role_permissions(self):
        """Refresh permissions for selected role"""
        role_id = self.role_combo.currentData()
        if role_id is None:
            return
            
        permissions = self.db.get_role_permissions(role_id)
        self.role_table.setRowCount(len(permissions))
        
        for i, perm in enumerate(permissions):
            name_item = QTableWidgetItem(perm['name'])
            desc_item = QTableWidgetItem(perm['description'])
            
            # Create checkbox for granted column
            checkbox = QCheckBox()
            checkbox.setChecked(bool(perm['granted']))
            checkbox.stateChanged.connect(lambda state, r=i: self.handle_permission_change(r, state))
            
            self.role_table.setItem(i, 0, name_item)
            self.role_table.setItem(i, 1, desc_item)
            self.role_table.setCellWidget(i, 2, checkbox)
            
            # Store permission code in name item
            name_item.setData(Qt.ItemDataRole.UserRole, perm['code'])
            
    def handle_permission_change(self, row: int, state: int):
        """Handle permission checkbox change"""
        role_id = self.role_combo.currentData()
        if role_id is None:
            return
            
        # Get all granted permissions
        granted_permissions = []
        for i in range(self.role_table.rowCount()):
            checkbox = self.role_table.cellWidget(i, 2)
            if checkbox.isChecked():
                name_item = self.role_table.item(i, 0)
                permission_code = name_item.data(Qt.ItemDataRole.UserRole)
                granted_permissions.append(permission_code)
                
        # Update permissions in database
        self.db.set_role_permissions(role_id, granted_permissions)
        
        # Refresh the role permissions table
        self.refresh_role_permissions()
        
    def setup_user_table(self):
        """Setup the user permissions table."""
        headers = ["الصلاحية", "الوصف", "ممنوحة", "منحت بواسطة"]
        self.user_table.setColumnCount(len(headers))
        self.user_table.setHorizontalHeaderLabels(headers)
        self.user_table.setAlternatingRowColors(True)
        self.user_table.horizontalHeader().setStretchLastSection(True)
        self.user_table.verticalHeader().setVisible(False)
        
        # Set column widths
        self.user_table.setColumnWidth(0, 250)  # Permission name
        self.user_table.setColumnWidth(1, 350)  # Description
        self.user_table.setColumnWidth(2, 120)  # Granted
        self.user_table.setColumnWidth(3, 200)  # Granted by
        
    def load_users(self):
        """تحميل قائمة الموظفين مع تحديث الذاكرة المؤقتة"""
        self.employees_cache = self.db.get_all_employees()  # حفظ نسخة مؤقتة
        self.user_combo.clear()
        self.user_combo.addItem("-- اختر الموظف --", None)
        for user in self.employees_cache:
            department = user.get('department_name') or user.get('department', '')
            self.user_combo.addItem(f"{user['name']} ({department})", user['id'])
            
    def refresh_user_permissions(self):
        """Refresh the user permissions table."""
        employee_id = self.user_combo.currentData()
        if not employee_id:
            return
            
        # Get user permissions
        permissions = self.db.get_user_permissions(employee_id)
        
        self.user_table.setRowCount(len(permissions))
        for i, permission in enumerate(permissions):
            # Permission name with custom style
            name_item = QTableWidgetItem(permission['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setForeground(QColor("#495057"))
            self.user_table.setItem(i, 0, name_item)
            
            # Description with custom style
            desc_item = QTableWidgetItem(permission['description'])
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            desc_item.setForeground(QColor("#6c757d"))
            self.user_table.setItem(i, 1, desc_item)
            
            # Checkbox for granted status
            checkbox = QCheckBox()
            checkbox.setChecked(permission['is_additional'])
            checkbox.stateChanged.connect(
                lambda state, e=employee_id, p=permission['id']: 
                self.toggle_user_permission(e, p, state)
            )
            
            # Center the checkbox
            checkbox_container = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_container)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            
            self.user_table.setCellWidget(i, 2, checkbox_container)
            
            # Granted by with custom style
            granted_by = permission['granted_by_name'] if permission['is_additional'] else '-'
            granted_item = QTableWidgetItem(granted_by)
            granted_item.setFlags(granted_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            granted_item.setForeground(QColor("#6c757d"))
            granted_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.user_table.setItem(i, 3, granted_item)
            
    def toggle_user_permission(self, employee_id: str, permission_id: int, state: int):
        """Toggle an additional permission for a user."""
        try:
            # Get the current user ID from the database
            current_user = self.db.get_current_user()
            if not current_user:
                QMessageBox.warning(
                    self, 
                    "خطأ",
                    "يجب تسجيل الدخول أولاً",
                    QMessageBox.StandardButton.Ok
                )
                self.refresh_user_permissions()
                return

            # Check if current user has permission to manage roles
            if not self.db.has_permission(current_user['id'], 'manage_roles'):
                QMessageBox.warning(
                    self, 
                    "خطأ",
                    "ليس لديك صلاحية لإدارة الصلاحيات",
                    QMessageBox.StandardButton.Ok
                )
                self.refresh_user_permissions()
                return
                
            if state == Qt.CheckState.Checked.value:
                if not self.db.grant_user_permission(employee_id, permission_id, current_user['id']):
                    QMessageBox.warning(
                        self, 
                        "خطأ",
                        "فشل منح الصلاحية للمستخدم",
                        QMessageBox.StandardButton.Ok
                    )
            else:
                if not self.db.revoke_user_permission(employee_id, permission_id, current_user['id']):
                    QMessageBox.warning(
                        self, 
                        "خطأ",
                        "فشل إلغاء الصلاحية من المستخدم",
                        QMessageBox.StandardButton.Ok
                    )
                    
            self.refresh_user_permissions()
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "خطأ",
                f"حدث خطأ أثناء تحديث الصلاحيات: {str(e)}",
                QMessageBox.StandardButton.Ok
            ) 

    def refresh_data(self):
        self.load_users()
        self.refresh_user_permissions() 