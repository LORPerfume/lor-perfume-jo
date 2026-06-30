# Sarh Enterprise Order System

نسخة احترافية جاهزة للرفع على GitHub و Render.

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

## بيانات الدخول التجريبية

- username: admin
- password: admin12345

## Render

يوجد ملف `render.yaml` جاهز. أسهل طريقة:

1. ارفع المشروع كامل على GitHub.
2. من Render اختر New Blueprint.
3. اختر المستودع.
4. Render سيقرأ `render.yaml` تلقائياً.

أو في Web Service عادي:

Build Command:

```bash
./build.sh
```

Start Command:

```bash
gunicorn order_system.wsgi:application
```

## ملاحظات مهمة

- لا ترفع مجلد venv.
- لا ترفع db.sqlite3 إذا كان الهدف إنتاجي.
- النسخة تدعم PostgreSQL تلقائياً عبر DATABASE_URL على Render.
