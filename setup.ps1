# إنشاء بيئة افتراضية وتثبيت الاعتماديات
python -m venv venv

# تفعيل البيئة الافتراضية (ملحوظة: تأكد من امتلاك الصلاحيات لتشغيل السكريبت)
.\venv\Scripts\Activate.ps1

# ترقية pip وتثبيت الاعتماديات
pip install --upgrade pip
pip install -r requirements.txt 