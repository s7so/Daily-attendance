import unittest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QMessageBox
from datetime import datetime
from src.ui.tabs.attendance_tab import AttendanceTab
from src.database.departments_db import DepartmentsDatabase

class TestAttendanceTab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """إعداد بيئة الاختبار للكل"""
        # إنشاء تطبيق Qt للاختبار
        cls.app = QApplication([])
        
    def setUp(self):
        """إعداد بيئة الاختبار لكل حالة"""
        # إنشاء قاعدة بيانات وهمية للاختبار
        self.db = DepartmentsDatabase(":memory:")
        
        # إنشاء نافذة الحضور والانصراف
        self.tab = AttendanceTab(self.db)
        
    def tearDown(self):
        """تنظيف بيئة الاختبار"""
        self.db.close()
        
    @classmethod
    def tearDownClass(cls):
        """تنظيف بيئة الاختبار للكل"""
        cls.app.quit()
        
    def test_initial_state(self):
        """اختبار الحالة الأولية للنافذة"""
        # التحقق من وجود العناصر الرئيسية
        self.assertIsNotNone(self.tab.ip_input)
        self.assertIsNotNone(self.tab.port_input)
        self.assertIsNotNone(self.tab.connect_btn)
        self.assertIsNotNone(self.tab.sync_btn)
        self.assertIsNotNone(self.tab.disconnect_btn)
        self.assertIsNotNone(self.tab.status_label)
        self.assertIsNotNone(self.tab.emp_combo)
        self.assertIsNotNone(self.tab.check_in_btn)
        self.assertIsNotNone(self.tab.check_out_btn)
        self.assertIsNotNone(self.tab.records_table)
        
        # التحقق من الحالة الأولية
        self.assertEqual(self.tab.status_label.text(), "غير متصل")
        self.assertEqual(self.tab.emp_combo.count(), 1)  # فقط العنصر الافتراضي
        
    @patch('src.devices.fingertec.FingertecDevice.connect')
    def test_handle_connect(self, mock_connect):
        """اختبار عملية الاتصال بالجهاز"""
        # تجهيز البيانات
        self.tab.ip_input.setText("192.168.1.100")
        self.tab.port_input.setValue(4370)
        mock_connect.return_value = True
        
        # تنفيذ الاتصال
        self.tab.handle_connect()
        
        # التحقق من النتائج
        mock_connect.assert_called_once()
        self.assertEqual(self.tab.status_label.text(), "متصل")
        
    @patch('src.devices.fingertec.FingertecDevice.disconnect')
    def test_handle_disconnect(self, mock_disconnect):
        """اختبار عملية قطع الاتصال"""
        # تنفيذ قطع الاتصال
        self.tab.handle_disconnect()
        
        # التحقق من النتائج
        mock_disconnect.assert_called_once()
        self.assertEqual(self.tab.status_label.text(), "غير متصل")
        
    @patch('src.devices.fingertec.FingertecDevice')
    def test_handle_sync(self, mock_device):
        """اختبار عملية المزامنة"""
        # تجهيز البيانات
        mock_device.return_value.connected = True
        mock_device.return_value.get_all_users.return_value = [
            {'id': '1001', 'name': 'أحمد'}
        ]
        mock_device.return_value.get_user_photo.return_value = b"test_photo"
        mock_device.return_value.get_attendance_logs.return_value = [
            {
                'employee_id': '1001',
                'timestamp': datetime.now(),
                'type': 'check_in'
            }
        ]
        
        # تنفيذ المزامنة
        with patch.object(QMessageBox, 'information') as mock_info:
            self.tab.handle_sync()
            mock_info.assert_called_once()
        
    def test_handle_check_in(self):
        """اختبار تسجيل الحضور"""
        # إضافة موظف للاختبار
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name) VALUES (?, ?)",
            ("1001", "أحمد")
        )
        self.tab.load_employees()
        
        # اختيار الموظف
        self.tab.emp_combo.setCurrentText("أحمد")
        
        # تنفيذ تسجيل الحضور
        with patch.object(QMessageBox, 'information') as mock_info:
            self.tab.handle_check_in()
            mock_info.assert_called_once()
            
        # التحقق من إضافة السجل
        records = self.db.get_today_attendance()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['name'], "أحمد")
        
    def test_handle_check_out(self):
        """اختبار تسجيل الانصراف"""
        # إضافة موظف للاختبار
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name) VALUES (?, ?)",
            ("1001", "أحمد")
        )
        self.tab.load_employees()
        
        # اختيار الموظف
        self.tab.emp_combo.setCurrentText("أحمد")
        
        # تنفيذ تسجيل الانصراف
        with patch.object(QMessageBox, 'information') as mock_info:
            self.tab.handle_check_out()
            mock_info.assert_called_once()
            
        # التحقق من إضافة السجل
        records = self.db.get_today_attendance()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['name'], "أحمد")
        
    def test_load_employees(self):
        """اختبار تحميل قائمة الموظفين"""
        # إضافة موظفين للاختبار
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name) VALUES (?, ?)",
            ("1001", "أحمد")
        )
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name) VALUES (?, ?)",
            ("1002", "محمد")
        )
        
        # تحميل الموظفين
        self.tab.load_employees()
        
        # التحقق من تحميل الموظفين
        self.assertEqual(self.tab.emp_combo.count(), 3)  # 2 موظفين + العنصر الافتراضي
        
    def test_refresh_records(self):
        """اختبار تحديث سجلات الحضور"""
        # إضافة موظف وسجل حضور للاختبار
        self.db.execute_query_with_commit(
            "INSERT INTO employees (id, name) VALUES (?, ?)",
            ("1001", "أحمد")
        )
        self.db.add_attendance(
            "1001",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "check_in"
        )
        
        # تحديث السجلات
        self.tab.refresh_records()
        
        # التحقق من تحديث الجدول
        self.assertEqual(self.tab.records_table.rowCount(), 1)
        
    @patch('src.devices.fingertec.FingertecDevice')
    def test_poll_device(self, mock_device):
        """اختبار جلب البيانات الدوري من الجهاز"""
        # تجهيز البيانات
        mock_device.return_value.connected = True
        mock_device.return_value.get_attendance_logs.return_value = [
            {
                'employee_id': '1001',
                'timestamp': datetime.now(),
                'type': 'check_in'
            }
        ]
        
        # تنفيذ الجلب الدوري
        self.tab.poll_device()
        
        # التحقق من تحديث السجلات
        mock_device.return_value.get_attendance_logs.assert_called_once()
        
if __name__ == '__main__':
    unittest.main() 