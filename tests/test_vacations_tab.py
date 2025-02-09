import pytest
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
from PyQt6.QtCore import Qt, QDate
from unittest.mock import MagicMock, patch

# تهيئة تطبيق Qt
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()

# تهيئة مشتركة لجميع الاختبارات
@pytest.fixture
def mock_db():
    db = MagicMock()
    
    # بيانات الإجازات الوهمية
    db.get_vacation_types.return_value = [
        {'id': 1, 'name': 'إجازة مرضية'},
        {'id': 2, 'name': 'إجازة سنوية'}
    ]
    
    db.get_all_employees.return_value = [
        {'id': 'EMP001', 'name': 'موظف 1', 'department_name': 'قسم الموارد البشرية'},
        {'id': 'EMP002', 'name': 'موظف 2', 'department_name': 'قسم تقنية المعلومات'}
    ]
    
    db.get_employee_vacations.return_value = [
        {
            'id': 1,
            'employee_id': 'EMP001',
            'type_id': 1,
            'start_date': '2024-01-01',
            'end_date': '2024-01-05',
            'status': 'معلقة'
        }
    ]
    
    return db

@pytest.fixture
def vacations_tab(mock_db, qapp):
    from src.ui.tabs.vacations_tab import VacationsTab
    tab = VacationsTab(mock_db)
    
    # إعادة تعيين عدادات الاستدعاء
    mock_db.get_vacation_types.reset_mock()
    mock_db.get_all_employees.reset_mock()
    mock_db.get_employee_vacations.reset_mock()
    
    yield tab
    tab.vacation_table.clearContents()

# اختبارات التهيئة الأساسية
def test_init_vacations_tab(vacations_tab):
    """اختبار تهيئة شاشة الإجازات"""
    assert vacations_tab is not None
    assert vacations_tab.vacation_table is not None
    assert vacations_tab.employee_combo is not None

# اختبار تحميل أنواع الإجازات
def test_load_vacation_types(vacations_tab, mock_db):
    """اختبار تحميل أنواع الإجازات"""
    mock_db.get_vacation_types.reset_mock()
    vacations_tab.load_vacation_types()
    assert vacations_tab.type_combo.count() == 2
    mock_db.get_vacation_types.assert_called_once()

# اختبار تحميل الموظفين
def test_load_employees(vacations_tab, mock_db):
    """اختبار تحميل قائمة الموظفين"""
    mock_db.get_all_employees.reset_mock()
    vacations_tab.load_employees()
    assert vacations_tab.employee_combo.count() == 2
    mock_db.get_all_employees.assert_called_once()

# اختبار إضافة إجازة جديدة
def test_add_vacation(vacations_tab, mock_db):
    """اختبار إضافة إجازة جديدة"""
    mock_db.add_vacation.return_value = True
    
    # تعيين القيم الوهمية
    vacations_tab.employee_combo.addItem("موظف 1", "EMP001")
    vacations_tab.type_combo.addItem("إجازة مرضية", 1)
    
    # تعيين التواريخ باستخدام QDate
    start_date = QDate(2024, 1, 1)
    end_date = QDate(2024, 1, 5)
    vacations_tab.start_date.setDate(start_date)
    vacations_tab.end_date.setDate(end_date)
    
    # تنفيذ الإضافة
    vacations_tab.add_vacation()
    
    # التحقق من الاستدعاء الصحيح
    mock_db.add_vacation.assert_called_once()
    call_args = mock_db.add_vacation.call_args[1]
    assert call_args['employee_id'] == 'EMP001'
    assert call_args['type_id'] == 1
    assert call_args['start_date'] == '2024-01-01'
    assert call_args['end_date'] == '2024-01-05'
    assert call_args['status'] == 'معلقة'

# اختبار تحديث جدول الإجازات
def test_refresh_vacations(vacations_tab, mock_db):
    """اختبار تحديث قائمة الإجازات"""
    mock_db.get_employee_vacations.reset_mock()
    vacations_tab.refresh_vacations()
    assert vacations_tab.vacation_table.rowCount() == 1
    mock_db.get_employee_vacations.assert_called_once()

# اختبار إلغاء إجازة
def test_cancel_vacation(vacations_tab, mock_db):
    """اختبار إلغاء إجازة"""
    mock_db.update_vacation_status.return_value = True
    
    # تحديد إجازة في الجدول
    vacations_tab.vacation_table.setRowCount(1)
    vacations_tab.vacation_table.setItem(0, 0, QTableWidgetItem("1"))
    vacations_tab.vacation_table.setCurrentCell(0, 0)
    
    # تنفيذ الإلغاء
    vacations_tab.cancel_vacation()
    
    # التحقق من تحديث الحالة
    mock_db.update_vacation_status.assert_called_once_with(1, 'ملغية')

# اختبار معالجة الأخطاء
def test_add_vacation_failure(vacations_tab, mock_db):
    """اختبار فشل إضافة إجازة"""
    mock_db.add_vacation.return_value = False
    with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
        vacations_tab.add_vacation()
        mock_warning.assert_called_once() 