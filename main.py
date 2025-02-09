import sys
import os
from PyQt6.QtWidgets import QApplication

# إضافة مسار المشروع للـ Python path
if getattr(sys, 'frozen', False):
    # نحن نعمل في وضع frozen/bundle
    application_path = sys._MEIPASS
else:
    # نحن نعمل في وضع التطوير العادي
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.append(application_path)

from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
