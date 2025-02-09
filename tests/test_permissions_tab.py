import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from unittest.mock import MagicMock, patch
from src.ui.tabs.permissions_tab import PermissionsTab

# إضافة تهيئة QApplication لكل الاختبارات
@pytest.fixture(scope="session")
def app():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def mock_db():
    db = MagicMock()
    
    # إعادة التعريف لكل اختبار
    db.get_all_roles.reset_mock()
    db.get_all_employees.reset_mock()
    db.get_all_permissions.reset_mock()
    db.get_role_permissions.reset_mock()
    db.get_user_permissions.reset_mock()
    
    # البيانات الوهمية
    db.get_all_roles.return_value = [
        {'id': 1, 'name': 'مدير'},
        {'id': 2, 'name': 'موظف'}
    ]
    
    db.get_all_employees.return_value = [
        {'id': 'EMP001', 'name': 'أحمد محمد', 'department_name': 'قسم الموارد البشرية'},
        {'id': 'EMP002', 'name': 'محمد علي', 'department_name': 'قسم تقنية المعلومات'}
    ]
    
    db.get_all_permissions.return_value = [
        {'id': 1, 'name': 'إدارة الموظفين', 'description': 'صلاحية إدارة الموظفين'},
        {'id': 2, 'name': 'إدارة الأقسام', 'description': 'صلاحية إدارة الأقسام'}
    ]
    
    db.get_role_permissions.return_value = [
        {'id': 1, 'name': 'إدارة الموظفين'}
    ]
    
    db.get_user_permissions.return_value = [
        {
            'id': 1,
            'name': 'إدارة الموظفين',
            'description': 'صلاحية إدارة الموظفين',
            'is_additional': True,
            'granted_by_name': 'المدير'
        }
    ]
    
    # إضافة جزء التنظيف
    yield db
    db.reset_mock()

@pytest.fixture
def permissions_tab(app, mock_db):
    tab = PermissionsTab(mock_db)
    # تحميل البيانات مرة واحدة فقط إذا لم تكن محملة
    if tab.role_combo.count() == 0:
        tab.load_roles()
    if tab.user_combo.count() == 0:
        tab.load_users()
    yield tab
    # تنظيف البيانات بعد كل اختبار
    tab.role_combo.clear()
    tab.user_combo.clear()
    # إعادة تعيين الموك
    mock_db.get_all_roles.reset_mock()
    mock_db.get_all_employees.reset_mock()

# اختبارات تهيئة الواجهة
def test_init_permissions_tab(permissions_tab):
    """اختبار التهيئة الأولية لصفحة الصلاحيات"""
    assert permissions_tab is not None
    assert permissions_tab.role_combo is not None
    assert permissions_tab.user_combo is not None
    assert permissions_tab.role_table is not None
    assert permissions_tab.user_table is not None

# اختبارات تحميل البيانات
def test_load_roles(permissions_tab, mock_db):
    """اختبار تحميل الأدوار"""
    # التحقق من عدد العناصر
    assert permissions_tab.role_combo.count() == 2
    # التحقق من استدعاء الدالة مرة واحدة
    mock_db.get_all_roles.assert_called_once()

def test_load_users(permissions_tab, mock_db):
    """اختبار تحميل المستخدمين"""
    # التحقق من عدد العناصر
    assert permissions_tab.user_combo.count() == 2
    # التحقق من استدعاء الدالة مرة واحدة
    mock_db.get_all_employees.assert_called_once()

# اختبارات تحديث الجداول
def test_refresh_role_permissions(permissions_tab, mock_db):
    """اختبار تحديث جدول صلاحيات الأدوار"""
    mock_db.get_all_permissions.reset_mock()  # إعادة تعيين العداد
    
    permissions_tab.role_combo.setCurrentIndex(0)
    permissions_tab.refresh_role_permissions()
    
    QApplication.processEvents()  # معالجة الأحداث المعلقة
    assert permissions_tab.role_table.rowCount() == 2
    mock_db.get_all_permissions.assert_called_once()

def test_refresh_user_permissions(permissions_tab, mock_db):
    """اختبار تحديث جدول صلاحيات المستخدمين"""
    mock_db.get_user_permissions.reset_mock()  # إعادة تعيين العداد
    
    permissions_tab.user_combo.setCurrentIndex(0)
    permissions_tab.refresh_user_permissions()
    
    QApplication.processEvents()  # معالجة الأحداث المعلقة
    assert permissions_tab.user_table.rowCount() == 1
    mock_db.get_user_permissions.assert_called_once_with('EMP001')

# اختبارات تبديل الصلاحيات
def test_toggle_role_permission_grant(permissions_tab, mock_db):
    """اختبار منح صلاحية لدور"""
    mock_db.assign_role_permission.return_value = True
    
    # تفعيل الصلاحية بشكل مباشر
    permissions_tab.toggle_role_permission(
        role_id=1,
        permission_id=1,
        state=Qt.CheckState.Checked.value
    )
    
    mock_db.assign_role_permission.assert_called_once_with(1, 1)

def test_toggle_role_permission_revoke(permissions_tab, mock_db):
    """اختبار إلغاء صلاحية من دور"""
    mock_db.revoke_role_permission.return_value = True
    permissions_tab.toggle_role_permission(1, 1, Qt.CheckState.Unchecked.value)
    mock_db.revoke_role_permission.assert_called_once_with(1, 1)

def test_toggle_user_permission_grant(permissions_tab, mock_db):
    """اختبار منح صلاحية إضافية لمستخدم"""
    mock_db.grant_user_permission.return_value = True
    permissions_tab.toggle_user_permission('EMP001', 1, Qt.CheckState.Checked.value)
    mock_db.grant_user_permission.assert_called_once()

def test_toggle_user_permission_revoke(permissions_tab, mock_db):
    """اختبار إلغاء صلاحية إضافية من مستخدم"""
    mock_db.revoke_user_permission.return_value = True
    permissions_tab.toggle_user_permission('EMP001', 1, Qt.CheckState.Unchecked.value)
    mock_db.revoke_user_permission.assert_called_once()

# اختبارات معالجة الأخطاء
def test_toggle_role_permission_failure(permissions_tab, mock_db):
    """اختبار فشل منح صلاحية لدور"""
    mock_db.assign_role_permission.return_value = False
    with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
        permissions_tab.toggle_role_permission(1, 1, Qt.CheckState.Checked.value)
        mock_warning.assert_called_once()

def test_toggle_user_permission_failure(permissions_tab, mock_db):
    """اختبار فشل منح صلاحية لمستخدم"""
    mock_db.grant_user_permission.return_value = False
    with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
        permissions_tab.toggle_user_permission('EMP001', 1, Qt.CheckState.Checked.value)
        mock_warning.assert_called_once()

# اختبارات تحقق من صحة البيانات
def test_role_combo_data(permissions_tab):
    """اختبار صحة بيانات قائمة الأدوار"""
    permissions_tab.load_roles()
    assert permissions_tab.role_combo.currentData() == 1
    assert permissions_tab.role_combo.itemData(0) == 1
    assert permissions_tab.role_combo.itemData(1) == 2

def test_user_combo_data(permissions_tab):
    """اختبار صحة بيانات قائمة المستخدمين"""
    permissions_tab.load_users()
    assert permissions_tab.user_combo.currentData() == 'EMP001'
    assert permissions_tab.user_combo.itemData(0) == 'EMP001'
    assert permissions_tab.user_combo.itemData(1) == 'EMP002'

# اختبارات تنسيق الجداول
def test_role_table_setup(permissions_tab):
    """اختبار إعداد جدول صلاحيات الأدوار"""
    assert permissions_tab.role_table.columnCount() == 3
    headers = [permissions_tab.role_table.horizontalHeaderItem(i).text() for i in range(3)]
    assert headers == ['الصلاحية', 'الوصف', 'ممنوحة']

def test_user_table_setup(permissions_tab):
    """اختبار إعداد جدول صلاحيات المستخدمين"""
    assert permissions_tab.user_table.columnCount() == 4
    headers = [permissions_tab.user_table.horizontalHeaderItem(i).text() for i in range(4)]
    assert headers == ['الصلاحية', 'الوصف', 'ممنوحة', 'منحت بواسطة'] 