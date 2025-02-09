import os
import sys
import pytest
import coverage

# إضافة مسار المشروع الرئيسي إلى PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# متغير عام للتغطية
_cov = None

@pytest.fixture(scope='session', autouse=True)
def coverage_setup(request):
    """تهيئة تغطية الكود في بداية الاختبارات"""
    global _cov
    
    if not _cov:
        _cov = coverage.Coverage(
            branch=True,
            source=['src'],
            omit=[
                '*/tests/*',
                '*/migrations/*',
                '*/__init__.py',
                'src/main.py'
            ]
        )
        _cov.start()
        
    yield _cov
    
    if _cov:
        _cov.stop()
        _cov.save()
        
        print("\nCoverage Report:")
        _cov.report(show_missing=True)
        
        try:
            _cov.html_report(directory='coverage_report')
            print("\nHTML coverage report generated in coverage_report/")
        except Exception as e:
            print(f"\nError generating HTML report: {e}")

@pytest.fixture(scope='session')
def test_db():
    """إنشاء قاعدة بيانات اختبار مؤقتة"""
    db_path = ':memory:'  # استخدام قاعدة بيانات في الذاكرة
    from src.database.departments_db import DepartmentsDatabase
    db = DepartmentsDatabase(db_path)
    yield db
    db.close()
    
@pytest.fixture(scope='session')
def qt_app():
    """إنشاء تطبيق Qt للاختبار"""
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    yield app
    app.quit() 