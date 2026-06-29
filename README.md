# Sarh Order Management System

نظام عربي متكامل لإدارة شركة تبيع منتج واحد وتتعاون مع شركة توصيل.

## المزايا
- إدارة العملاء
- إدارة الطلبات وحالاتها
- شركات التوصيل وأسعار التوصيل
- متابعة العملاء والطلبات
- التحصيل والمدفوعات
- الصناديق النقدية وحركاتها
- الذمم المدينة
- مصاريف الشركة
- لوحة تحكم وتقارير مبسطة
- لوحة إدارة Django Admin كاملة

## التشغيل محلياً

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

افتح:
- النظام: http://127.0.0.1:8000
- لوحة الإدارة: http://127.0.0.1:8000/admin

## الرفع على GitHub

```bash
git init
git add .
git commit -m "Initial order management system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```
