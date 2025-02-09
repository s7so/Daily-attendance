import socket
import json
from datetime import datetime
from typing import Optional, Dict, List
import logging

class FingertecDevice:
    """فئة للتعامل مع جهاز Fingertec Face ID 5"""
    
    def __init__(self, ip: str = "10.20.2.4", port: int = 3000):
        self.ip = ip
        self.port = port
        self.connected = False
        self.socket: Optional[socket.socket] = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> bool:
        """الاتصال بالجهاز"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 5 seconds timeout
            self.socket.connect((self.ip, self.port))
            self.connected = True
            self.logger.info(f"Connected to Fingertec device at {self.ip}:{self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to device: {str(e)}")
            self.connected = False
            return False
            
    def disconnect(self):
        """قطع الاتصال بالجهاز"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        self.socket = None
        
    def get_attendance_logs(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        جلب سجلات الحضور من الجهاز
        في الوضع التجريبي، نقوم بإرجاع بيانات وهمية للاختبار
        """
        if not self.connected:
            return []
            
        try:
            # في الوضع الفعلي، سنقوم بإرسال الأمر للجهاز وانتظار الرد
            # حالياً نقوم بإرجاع بيانات وهمية للاختبار
            return [
                {
                    "employee_id": "EMP001",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "check_in",
                    "verified": True
                }
            ]
        except Exception as e:
            self.logger.error(f"Failed to get attendance logs: {str(e)}")
            return []
            
    def verify_face(self, employee_id: str) -> bool:
        """
        التحقق من بصمة الوجه
        في الوضع التجريبي، نقوم بإرجاع True دائماً
        """
        if not self.connected:
            return False
            
        try:
            # في الوضع الفعلي، سنقوم بإرسال الأمر للجهاز وانتظار الرد
            # حالياً نقوم بإرجاع True للاختبار
            return True
        except Exception as e:
            self.logger.error(f"Failed to verify face: {str(e)}")
            return False
            
    def add_employee(self, employee_id: str, name: str, face_data: bytes) -> bool:
        """
        إضافة موظف جديد للجهاز
        في الوضع التجريبي، نقوم بإرجاع True دائماً
        """
        if not self.connected:
            return False
            
        try:
            # في الوضع الفعلي، سنقوم بإرسال بيانات الموظف للجهاز
            # حالياً نقوم بإرجاع True للاختبار
            return True
        except Exception as e:
            self.logger.error(f"Failed to add employee: {str(e)}")
            return False
            
    def remove_employee(self, employee_id: str) -> bool:
        """
        حذف موظف من الجهاز
        في الوضع التجريبي، نقوم بإرجاع True دائماً
        """
        if not self.connected:
            return False
            
        try:
            # في الوضع الفعلي، سنقوم بإرسال أمر حذف الموظف للجهاز
            # حالياً نقوم بإرجاع True للاختبار
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove employee: {str(e)}")
            return False
            
    def sync_time(self) -> bool:
        """
        مزامنة وقت الجهاز مع وقت السيرفر
        في الوضع التجريبي، نقوم بإرجاع True دائماً
        """
        if not self.connected:
            return False
            
        try:
            # في الوضع الفعلي، سنقوم بإرسال الوقت الحالي للجهاز
            current_time = datetime.now()
            # حالياً نقوم بإرجاع True للاختبار
            return True
        except Exception as e:
            self.logger.error(f"Failed to sync time: {str(e)}")
            return False
            
    def get_device_info(self) -> Dict:
        """
        جلب معلومات الجهاز
        في الوضع التجريبي، نقوم بإرجاع بيانات وهمية
        """
        if not self.connected:
            return {}
            
        try:
            # في الوضع الفعلي، سنقوم بإرسال أمر جلب معلومات الجهاز
            # حالياً نقوم بإرجاع بيانات وهمية للاختبار
            return {
                "model": "Face ID 5",
                "serial": "FID5-001",
                "firmware": "v4.3.2",
                "total_users": 100,
                "used_memory": 50
            }
        except Exception as e:
            self.logger.error(f"Failed to get device info: {str(e)}")
            return {} 