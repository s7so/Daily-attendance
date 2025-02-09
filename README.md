# نظام إدارة الحضور والانصراف للموظفين

نظام متكامل لإدارة حضور وانصراف الموظفين، مكتوب بلغة Python باستخدام PyQt6 لواجهة المستخدم وSQLite لقاعدة البيانات.

## المميزات

- تسجيل الحضور والانصراف للموظفين
- إدارة الأقسام والموظفين
- نظام الورديات المرن
- تقارير الحضور والانصراف
- إدارة الإجازات والاستئذان
- نظام الصلاحيات المتعدد المستويات
- واجهة مستخدم عربية سهلة الاستخدام
- خيار "تذكرني" لتسهيل تسجيل الدخول
- دعم أجهزة البصمة (قريباً)

## المتطلبات

- Python 3.8 أو أحدث
- PyQt6
- SQLite3

## التثبيت

1. قم بنسخ المستودع:
```bash
git clone https://github.com/yourusername/Daily-attendance-program-for-employees---Python.git
cd Daily-attendance-program-for-employees---Python
```

2. قم بإنشاء بيئة Python افتراضية وتفعيلها:
```bash
python -m venv venv
source venv/bin/activate  # على Linux/Mac
# أو
venv\Scripts\activate  # على Windows
```

3. قم بتثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

4. قم بتشغيل البرنامج:
```bash
python main.py
```

## الاستخدام

1. عند تشغيل البرنامج لأول مرة، سيتم إنشاء حساب مدير النظام تلقائياً
   - اسم المستخدم: admin
   - كلمة المرور الافتراضية: Admin@2024

2. قم بتسجيل الدخول باستخدام حساب المدير
3. قم بإضافة الأقسام والموظفين والورديات حسب الحاجة
4. يمكن للموظفين تسجيل الدخول وتسجيل حضورهم وانصرافهم

## المساهمة

نرحب بمساهماتكم! يرجى اتباع الخطوات التالية:

1. قم بعمل Fork للمشروع
2. قم بإنشاء فرع جديد للميزة: `git checkout -b feature/amazing-feature`
3. قم بإجراء تغييراتك وإضافتها: `git add .`
4. قم بعمل commit: `git commit -m 'إضافة ميزة رائعة'`
5. قم برفع التغييرات: `git push origin feature/amazing-feature`
6. قم بإنشاء Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل.

## الاتصال

اسمك - [@حسابك_على_تويتر](https://twitter.com/حسابك)

رابط المشروع: [https://github.com/yourusername/Daily-attendance-program-for-employees---Python](https://github.com/yourusername/Daily-attendance-program-for-employees---Python) 