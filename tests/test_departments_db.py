import unittest
from unittest.mock import Mock, patch
import sqlite3
from datetime import datetime, date
from src.database.departments_db import DepartmentsDatabase

class TestDepartmentsDatabase(unittest.TestCase):
    def setUp(self):
        """إعداد بيئة الاختبار"""
        self.db = DepartmentsDatabase(":memory:")  # استخدام قاعدة بيانات في الذاكرة للاختبار
        
    def tearDown(self):
        """تنظيف بيئة الاختبار"""
        self.db.close()
        
    def test_connection(self):
        """اختبار الاتصال بقاعدة البيانات"""
        conn = self.db.get_connection()
        self.assertIsInstance(conn, sqlite3.Connection)
        self.assertTrue(conn.in_transaction)  # التأكد من أن الاتصال نشط
        
    def test_execute_query(self):
        """اختبار تنفيذ الاستعلامات"""
        # إدخال بيانات تجريبية
        self.db.execute_query_with_commit(
            "INSERT INTO departments (code, name) VALUES (?, ?)",
            ("IT", "تقنية المعلومات")
        )
        
        # استرجاع البيانات
        cursor = self.db.execute_query(
            "SELECT name FROM departments WHERE code = ?",
            ("IT",)
        )
        result = cursor.fetchone()
        self.assertEqual(result['name'], "تقنية المعلومات")
        
    def test_add_department(self):
        """اختبار إضافة قسم جديد"""
        # إضافة قسم بدون مدير
        result = self.db.add_department("HR", "الموارد البشرية")
        self.assertTrue(result)
        
        # التحقق من إضافة القسم
        dept = self.db.get_department("HR")
        self.assertEqual(dept['name'], "الموارد البشرية")
        self.assertIsNone(dept['manager_id'])
        
        # إضافة قسم بنفس الكود (يجب أن يفشل)
        result = self.db.add_department("HR", "قسم آخر")
        self.assertFalse(result)
        
    def test_update_department(self):
        """اختبار تحديث معلومات القسم"""
        # إضافة قسم للاختبار
        self.db.add_department("IT", "تقنية المعلومات")
        
        # تحديث اسم القسم
        result = self.db.update_department("IT", "تكنولوجيا المعلومات")
        self.assertTrue(result)
        
        # التحقق من التحديث
        dept = self.db.get_department("IT")
        self.assertEqual(dept['name'], "تكنولوجيا المعلومات")
        
    def test_delete_department(self):
        """اختبار حذف قسم"""
        # إضافة قسم للاختبار
        self.db.add_department("TEST", "قسم اختباري")
        
        # حذف القسم
        result = self.db.delete_department("TEST")
        self.assertTrue(result)
        
        # التحقق من الحذف
        dept = self.db.get_department("TEST")
        self.assertIsNone(dept)
        
    def test_get_all_departments(self):
        """اختبار جلب جميع الأقسام"""
        # إضافة أقسام للاختبار
        self.db.add_department("IT", "تقنية المعلومات")
        self.db.add_department("HR", "الموارد البشرية")
        
        # جلب جميع الأقسام
        departments = self.db.get_all_departments()
        self.assertEqual(len(departments), 2)
        self.assertEqual(departments[0]['code'], "HR")  # مرتبة حسب الاسم
        self.assertEqual(departments[1]['code'], "IT")
        
    def test_get_department_employees(self):
        """اختبار جلب موظفي قسم معين"""
        # إضافة قسم وموظفين للاختبار
        self.db.add_department("IT", "تقنية المعلومات")
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name, department_code, role_id) VALUES (?, ?, ?, ?)",
            ("1001", "أحمد", "IT", 1)
        )
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name, department_code, role_id) VALUES (?, ?, ?, ?)",
            ("1002", "محمد", "IT", 1)
        )
        
        # جلب موظفي القسم
        employees = self.db.get_department_employees("IT")
        self.assertEqual(len(employees), 2)
        self.assertEqual(employees[0]['name'], "أحمد")
        self.assertEqual(employees[1]['name'], "محمد")
        
    def test_transfer_employee(self):
        """اختبار نقل موظف بين الأقسام"""
        # إضافة أقسام وموظف للاختبار
        self.db.add_department("IT", "تقنية المعلومات")
        self.db.add_department("HR", "الموارد البشرية")
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name, department_code, role_id) VALUES (?, ?, ?, ?)",
            ("1001", "أحمد", "IT", 1)
        )
        
        # نقل الموظف
        result = self.db.transfer_employee("1001", "HR")
        self.assertTrue(result)
        
        # التحقق من النقل
        cursor = self.db.execute_query(
            "SELECT department_code FROM employees WHERE id = ?",
            ("1001",)
        )
        self.assertEqual(cursor.fetchone()['department_code'], "HR")
        
    def test_get_roles(self):
        """اختبار جلب الأدوار الوظيفية"""
        roles = self.db.get_roles()
        self.assertTrue(len(roles) >= 2)  # الأدوار الافتراضية
        self.assertEqual(roles[0]['name'], "مدير")
        self.assertEqual(roles[1]['name'], "موظف")
        
    def test_add_role(self):
        """اختبار إضافة دور وظيفي"""
        result = self.db.add_role("مشرف")
        self.assertTrue(result)
        
        # التحقق من الإضافة
        roles = self.db.get_roles()
        role_names = [r['name'] for r in roles]
        self.assertIn("مشرف", role_names)
        
    def test_get_managers(self):
        """اختبار جلب المدراء"""
        # إضافة قسم ومدير للاختبار
        self.db.add_department("IT", "تقنية المعلومات")
        self.db.execute_query_with_commit(
            """
            INSERT INTO employees (id, name, department_code, role_id)
            SELECT '1001', 'أحمد', 'IT', id
            FROM roles WHERE name = 'مدير'
            """
        )
        
        # جلب المدراء
        managers = self.db.get_managers()
        self.assertEqual(len(managers), 1)
        self.assertEqual(managers[0]['name'], "أحمد")
        
    def test_add_employee_status(self):
        """اختبار إضافة حالة للموظف"""
        # إضافة قسم للاختبار
        self.db.add_department("IT", "تقنية المعلومات")
        
        # إضافة موظف للاختبار
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name, department_code, role_id) VALUES (?, ?, ?, ?)",
            ("1001", "أحمد", "IT", 1)
        )
        
        # إضافة نوع الحالة للاختبار
        self.db.execute_query_with_commit(
            "INSERT INTO status_types (id, name, requires_approval) VALUES (?, ?, ?)",
            (1, "إجازة سنوية", True)
        )
        
        # إضافة حالة
        result = self.db.add_employee_status(
            "1001",
            1,  # إجازة سنوية
            "2024-01-01",
            "2024-01-07",
            "إجازة سنوية"
        )
        self.assertTrue(result)
        
    def test_get_today_attendance(self):
        """اختبار جلب سجلات حضور اليوم"""
        # إضافة قسم للاختبار
        self.db.add_department("IT", "تقنية المعلومات")
        
        # إضافة موظف وسجل حضور للاختبار
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name, department_code, role_id) VALUES (?, ?, ?, ?)",
            ("1001", "أحمد", "IT", 1)
        )
        
        today = date.today()
        self.db.add_attendance(
            "1001",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "check_in"
        )
        
        # جلب سجلات اليوم
        records = self.db.get_today_attendance()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['name'], "أحمد")
        
    def test_save_and_get_employee_photo(self):
        """اختبار حفظ وجلب صورة الموظف"""
        # إضافة موظف للاختبار
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name) VALUES (?, ?)",
            ("1001", "أحمد")
        )
        
        # حفظ صورة
        photo_data = b"test_photo_data"
        result = self.db.save_employee_photo("1001", photo_data)
        self.assertTrue(result)
        
        # جلب الصورة
        saved_photo = self.db.get_employee_photo("1001")
        self.assertEqual(saved_photo, photo_data)
        
if __name__ == '__main__':
    unittest.main() 