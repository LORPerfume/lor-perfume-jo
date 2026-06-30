# LOR FollowUp Pro

نظام متابعة شخصي/CRM عربي مبني بـ Django. ليس متجرًا، بل لوحة متابعة لإدارة العملاء، المعاملات، المهام، المتابعات، الملاحظات، الملفات، المالية، والتقارير.

## أهم الإضافات

- Dashboard تنفيذية مع تنبيهات المتابعات والمهام المتأخرة.
- ملف عميل كامل مع Timeline لكل نشاط.
- بحث ذكي عام Ctrl+K.
- مهام ToDo مع أولوية وحالة واستحقاق.
- متابعات Follow-up مع مواعيد قادمة ومتأخرة.
- ملاحظات وملفات مرفقة لكل عميل/معاملة.
- مالية: صناديق، دفعات، مصاريف، ذمم، صافي شهري.
- تقويم مبسط للمتابعات والمهام والاستحقاقات.
- تقارير وتصدير CSV يفتح على Excel.
- واجهة RTL حديثة ومتجاوبة.

## التشغيل المحلي

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

افتح: http://127.0.0.1:8000

بيانات الدخول التجريبية:

- username: admin
- password: admin12345

## Render

Build Command:

```bash
./build.sh
```

Start Command:

```bash
gunicorn order_system.wsgi:application
```

## ملاحظات أمان مهمة

- غيّر كلمة مرور admin فورًا.
- لا ترفع db.sqlite3 للإنتاج.
- استخدم متغيرات بيئة SECRET_KEY و DEBUG=False و DATABASE_URL.

## إصلاح مهم لـ Render

تمت إضافة migration باسم:

```bash
core/migrations/0002_repair_existing_render_schema.py
```

هذه تعالج قواعد البيانات الموجودة مسبقاً على Render والتي كان لديها `core.0001_initial` من النسخة القديمة، وتضيف الأعمدة/الجداول الجديدة مثل `customer.email` و `Task` و `Note` و `Attachment` بدون حذف البيانات.

بعد رفع هذه النسخة إلى GitHub، اعمل Deploy فقط. أمر البناء الموجود سيشغل:

```bash
python manage.py migrate
```

والمشكلة التي كانت تظهر:

```text
column core_customer.email does not exist
```

ستنحل.
