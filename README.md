# نظام إدارة الحضور والانصراف للموظفين 👥

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/s7so/Daily-attendance?style=social)
![GitHub forks](https://img.shields.io/github/forks/s7so/Daily-attendance?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/s7so/Daily-attendance?style=social)
![GitHub](https://img.shields.io/github/license/s7so/Daily-attendance)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![PyQt Version](https://img.shields.io/badge/PyQt-6.0%2B-green)

</div>

<div dir="rtl">

## 📝 نظرة عامة

نظام متكامل لإدارة حضور وانصراف الموظفين، مصمم خصيصاً للشركات والمؤسسات التي تحتاج إلى نظام موثوق وسهل الاستخدام لتتبع دوام موظفيها. النظام مكتوب بلغة Python مع واجهة مستخدم رسومية باستخدام PyQt6 وقاعدة بيانات SQLite.

## ✨ المميزات الرئيسية

### 🔐 نظام تسجيل الدخول والأمان
- نظام تسجيل دخول آمن متعدد المستويات
- خيار "تذكرني" لتسهيل تسجيل الدخول
- إدارة الصلاحيات والأدوار المختلفة
- تشفير كلمات المرور وحماية البيانات

### 👥 إدارة الموظفين والأقسام
- إضافة وتعديل وحذف الموظفين
- تنظيم الموظفين في أقسام
- إدارة المناصب والمسميات الوظيفية
- تتبع تاريخ نقل الموظفين بين الأقسام

### ⏰ نظام الورديات المرن
- إنشاء ورديات عمل مخصصة
- تحديد أوقات الدوام والاستراحات
- دعم الدوام المرن
- إمكانية تعيين ورديات متعددة للموظف

### 📊 التقارير والإحصائيات
- تقارير الحضور اليومية والشهرية
- تقارير التأخير والغياب
- تقارير الإجازات والاستئذانات
- تصدير التقارير بصيغ مختلفة (PDF, Excel)

### 🚀 ميزات قادمة
- [ ] دعم أجهزة البصمة
- [ ] تطبيق موبايل للموظفين
- [ ] نظام الإشعارات
- [ ] التكامل مع أنظمة الرواتب

## 💻 المتطلبات التقنية

### متطلبات النظام
- نظام تشغيل: Windows, Linux, أو macOS
- Python 3.8 أو أحدث
- مساحة تخزين: 100MB على الأقل
- ذاكرة RAM: 2GB على الأقل

### المكتبات المطلوبة
```plaintext
PyQt6==6.4.0
SQLite3
pandas>=1.3.0
openpyxl>=3.0.0
```

## ⚙️ التثبيت

### 1. نسخ المستودع
```bash
git clone https://github.com/s7so/Daily-attendance.git
cd Daily-attendance
```

### 2. إنشاء وتفعيل البيئة الافتراضية
```bash
# إنشاء البيئة الافتراضية
python -m venv venv

# تفعيل البيئة - Windows
venv\Scripts\activate

# تفعيل البيئة - Linux/Mac
source venv/bin/activate
```

### 3. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 4. تشغيل البرنامج
```bash
python main.py
```

## 🎯 كيفية الاستخدام

### الإعداد الأولي
1. عند تشغيل البرنامج لأول مرة، سيتم إنشاء حساب مدير النظام تلقائياً:
   - اسم المستخدم: `admin`
   - كلمة المرور: `Admin@2024`

### خطوات البدء
1. قم بتسجيل الدخول كمدير نظام
2. أضف الأقسام الرئيسية للشركة
3. قم بإعداد الورديات المطلوبة
4. أضف الموظفين وعين لهم الأقسام والورديات
5. ابدأ باستخدام النظام لتسجيل الحضور والانصراف

## 🤝 المساهمة

نرحب بمساهماتكم في تطوير المشروع! إليك كيفية المساهمة:

1. قم بعمل Fork للمشروع
2. قم بإنشاء فرع جديد للميزة: `git checkout -b feature/amazing-feature`
3. قم بإجراء تغييراتك وإضافتها: `git add .`
4. قم بعمل commit: `git commit -m 'إضافة ميزة رائعة'`
5. قم برفع التغييرات: `git push origin feature/amazing-feature`
6. قم بإنشاء Pull Request

## 📝 الترخيص

هذا المشروع مرخص تحت رخصة MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل.

## 📞 الدعم والتواصل

- المطور: s7so
- GitHub: [@s7so](https://github.com/s7so)
- البريد الإلكتروني: [your.email@example.com](mailto:your.email@example.com)

## 🌟 شكر خاص

شكر خاص لكل المساهمين في هذا المشروع وللمجتمع البرمجي العربي.

---

<div align="center">

**صنع بـ ❤️ في السعودية 🇸🇦**

</div>

</div> 