from PyQt6.QtWidgets import (
    QWidget, 
    QTableWidget, 
    QHeaderView, 
    QTableWidgetItem,
    QComboBox,
    QDateEdit,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt, QDate

class VacationsTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """تهيئة واجهة إدارة الإجازات"""
        layout = QVBoxLayout()
        
        # إنشاء العناصر الأساسية
        controls_layout = QHBoxLayout()
        
        self.employee_combo = QComboBox()
        self.type_combo = QComboBox()
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        
        # تهيئة التواريخ
        self.start_date.setDate(QDate.currentDate())
        self.end_date.setDate(QDate.currentDate())
        
        controls_layout.addWidget(self.employee_combo)
        controls_layout.addWidget(self.type_combo)
        controls_layout.addWidget(self.start_date)
        controls_layout.addWidget(self.end_date)
        
        # أزرار التحكم
        add_button = QPushButton("إضافة إجازة")
        add_button.clicked.connect(self.add_vacation)
        cancel_button = QPushButton("إلغاء إجازة")
        cancel_button.clicked.connect(self.cancel_vacation)
        
        controls_layout.addWidget(add_button)
        controls_layout.addWidget(cancel_button)
        
        layout.addLayout(controls_layout)
        
        # إنشاء الجدول
        self.vacation_table = QTableWidget()
        self.vacation_table.setColumnCount(6)
        self.vacation_table.setHorizontalHeaderLabels([
            'ID', 'الموظف', 'نوع الإجازة', 'تاريخ البدء', 'تاريخ الانتهاء', 'الحالة'
        ])
        self.vacation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.vacation_table)
        self.setLayout(layout)
        
    def load_data(self):
        """تحميل البيانات الأولية"""
        self.load_employees()
        self.load_vacation_types()
        self.refresh_vacations()
        
    def load_employees(self):
        """تحميل قائمة الموظفين"""
        employees = self.db.get_all_employees()
        self.employee_combo.clear()
        self.employee_combo.addItem("-- اختر الموظف --", None)
        for emp in employees:
            department = emp.get('department_name') or emp.get('department', '')
            self.employee_combo.addItem(f"{emp['name']} ({department})", emp['id'])
        
    def load_vacation_types(self):
        """تحميل أنواع الإجازات"""
        types = self.db.get_status_types()
        self.type_combo.clear()
        self.type_combo.addItem("-- اختر نوع الإجازة --", None)
        for t in types:
            if t['name'].startswith('إجازة'):
                self.type_combo.addItem(t['name'], t['id'])
        
    def refresh_vacations(self):
        """تحديث قائمة الإجازات"""
        vacations = self.db.get_all_status()
        self.vacation_table.setRowCount(0)
        
        for vac in vacations:
            # تجاهل السجلات التي ليست إجازات
            status_type = vac.get('status_type', '')
            if not status_type.startswith('إجازة'):
                continue
                
            row = self.vacation_table.rowCount()
            self.vacation_table.insertRow(row)
            
            # تحديد حالة الإجازة
            status = 'معلقة'
            if vac.get('approved') is True:
                status = 'موافق عليها'
            elif vac.get('approved') is False:
                status = 'مرفوضة'
                
            # إضافة البيانات للجدول مع التحقق من وجود المفاتيح
            self.vacation_table.setItem(row, 0, QTableWidgetItem(str(vac.get('id', ''))))
            self.vacation_table.setItem(row, 1, QTableWidgetItem(vac.get('employee_name', '')))
            self.vacation_table.setItem(row, 2, QTableWidgetItem(status_type))
            self.vacation_table.setItem(row, 3, QTableWidgetItem(vac.get('start_date', '')))
            self.vacation_table.setItem(row, 4, QTableWidgetItem(vac.get('end_date', '')))
            self.vacation_table.setItem(row, 5, QTableWidgetItem(status))
            
    def add_vacation(self):
        """إضافة إجازة جديدة"""
        try:
            employee_id = self.employee_combo.currentData()
            type_id = self.type_combo.currentData()
            start_date = self.start_date.date().toString('yyyy-MM-dd')
            end_date = self.end_date.date().toString('yyyy-MM-dd')
            
            if not employee_id or not type_id:
                raise Exception("الرجاء اختيار الموظف ونوع الإجازة")
                
            if self.start_date.date() > self.end_date.date():
                raise Exception("تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
                
            success = self.db.add_employee_status(
                employee_id=employee_id,
                status_type_id=type_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not success:
                raise Exception("فشل إضافة الإجازة")
                
            self.refresh_vacations()
            QMessageBox.information(
                self,
                "نجاح",
                "تم إضافة الإجازة بنجاح",
                QMessageBox.StandardButton.Ok
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "خطأ",
                str(e),
                QMessageBox.StandardButton.Ok
            )
            
    def cancel_vacation(self):
        """إلغاء إجازة محددة"""
        selected = self.vacation_table.currentRow()
        if selected < 0:
            QMessageBox.warning(
                self,
                "تنبيه",
                "الرجاء اختيار إجازة للإلغاء",
                QMessageBox.StandardButton.Ok
            )
            return
            
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل أنت متأكد من إلغاء هذه الإجازة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            status_id = int(self.vacation_table.item(selected, 0).text())
            if self.db.approve_employee_status(status_id, approved=False):
                self.refresh_vacations()
                QMessageBox.information(
                    self,
                    "نجاح",
                    "تم إلغاء الإجازة بنجاح",
                    QMessageBox.StandardButton.Ok
                )
            else:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    "فشل إلغاء الإجازة",
                    QMessageBox.StandardButton.Ok
                ) 