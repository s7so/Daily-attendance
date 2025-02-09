import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from src.devices.fingertec import FingertecDevice

class TestFingertecDevice(unittest.TestCase):
    def setUp(self):
        """إعداد بيئة الاختبار"""
        self.device = FingertecDevice()
        self.device.ip = "192.168.1.100"
        self.device.port = 4370
        
    @patch('socket.socket')
    def test_connect_success(self, mock_socket):
        """اختبار الاتصال الناجح بالجهاز"""
        # تجهيز المحاكاة
        mock_socket.return_value.connect.return_value = None
        mock_socket.return_value.send.return_value = len(b"test")
        mock_socket.return_value.recv.return_value = b"success"
        
        # تنفيذ الاختبار
        result = self.device.connect()
        
        # التحقق من النتائج
        self.assertTrue(result)
        self.assertTrue(self.device.connected)
        mock_socket.return_value.connect.assert_called_once_with((self.device.ip, self.device.port))
        
    @patch('socket.socket')
    def test_connect_failure(self, mock_socket):
        """اختبار فشل الاتصال بالجهاز"""
        # تجهيز المحاكاة
        mock_socket.return_value.connect.side_effect = Exception("Connection failed")
        
        # تنفيذ الاختبار
        result = self.device.connect()
        
        # التحقق من النتائج
        self.assertFalse(result)
        self.assertFalse(self.device.connected)
        
    def test_disconnect(self):
        """اختبار قطع الاتصال بالجهاز"""
        # تجهيز الحالة
        self.device.connected = True
        self.device.socket = Mock()
        
        # تنفيذ الاختبار
        self.device.disconnect()
        
        # التحقق من النتائج
        self.assertFalse(self.device.connected)
        self.device.socket.close.assert_called_once()
        
    @patch('socket.socket')
    def test_get_all_users(self, mock_socket):
        """اختبار جلب بيانات جميع المستخدمين"""
        # تجهيز المحاكاة
        mock_response = b"""1\t1001\tAhmed\t1\t\t\t\t
2\t1002\tMohamed\t1\t\t\t\t"""
        mock_socket.return_value.recv.return_value = mock_response
        self.device.connected = True
        self.device.socket = mock_socket.return_value
        
        # تنفيذ الاختبار
        users = self.device.get_all_users()
        
        # التحقق من النتائج
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0]['id'], '1001')
        self.assertEqual(users[0]['name'], 'Ahmed')
        self.assertEqual(users[1]['id'], '1002')
        self.assertEqual(users[1]['name'], 'Mohamed')
        
    @patch('socket.socket')
    def test_get_attendance_logs(self, mock_socket):
        """اختبار جلب سجلات الحضور"""
        # تجهيز المحاكاة
        mock_response = b"""1001\t2024-01-31 08:00:00\t0\t1\t
1002\t2024-01-31 17:00:00\t1\t1\t"""
        mock_socket.return_value.recv.return_value = mock_response
        self.device.connected = True
        self.device.socket = mock_socket.return_value
        
        # تنفيذ الاختبار
        start_date = datetime(2024, 1, 31)
        end_date = datetime(2024, 1, 31)
        logs = self.device.get_attendance_logs(start_date, end_date)
        
        # التحقق من النتائج
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0]['employee_id'], '1001')
        self.assertEqual(logs[0]['type'], 'check_in')
        self.assertEqual(logs[1]['employee_id'], '1002')
        self.assertEqual(logs[1]['type'], 'check_out')
        
    @patch('socket.socket')
    def test_get_user_photo(self, mock_socket):
        """اختبار جلب صورة المستخدم"""
        # تجهيز المحاكاة
        mock_photo_data = b"test_photo_data"
        mock_socket.return_value.recv.return_value = mock_photo_data
        self.device.connected = True
        self.device.socket = mock_socket.return_value
        
        # تنفيذ الاختبار
        photo = self.device.get_user_photo("1001")
        
        # التحقق من النتائج
        self.assertEqual(photo, mock_photo_data)
        
    def test_not_connected_operations(self):
        """اختبار العمليات عندما يكون الجهاز غير متصل"""
        self.device.connected = False
        
        # اختبار جلب المستخدمين
        self.assertEqual(self.device.get_all_users(), [])
        
        # اختبار جلب سجلات الحضور
        start_date = datetime.now()
        end_date = datetime.now()
        self.assertEqual(self.device.get_attendance_logs(start_date, end_date), [])
        
        # اختبار جلب صورة المستخدم
        self.assertIsNone(self.device.get_user_photo("1001"))
        
if __name__ == '__main__':
    unittest.main() 