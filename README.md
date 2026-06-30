# Sarh Pro Order Management System

نسخة احترافية عربية RTL لإدارة الطلبات، العملاء، المنتجات، المخزون، شركات التوصيل، التحصيل، الصناديق، المصاريف، المتابعات، والتقارير.

## المميزات المرعبة في النسخة الأولى
- Dashboard تنفيذية بتصميم حديث.
- إدارة عملاء CRM مع مصدر العميل والوسوم.
- إدارة منتجات ومخزون وتنبيهات انخفاض المخزون.
- إدارة طلبات بفلاتر متقدمة وحالات دفع وشحن وأولوية.
- دفعات وصناديق نقدية وحركات تلقائية.
- مصاريف وتقارير ربح وذمم ومبيعات.
- مركز متابعة العملاء والتذكيرات.
- فاتورة قابلة للطباعة لكل طلب.
- Django Admin احترافي لكل الجداول.
- صلاحية مخصصة للتقارير: `core.can_view_reports`.
- أمر بيانات تجريبية جاهز.

## التشغيل
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

افتح النظام:
http://127.0.0.1:8000

بيانات الدخول التجريبية:
- Username: admin
- Password: admin12345

## ملاحظات مهمة
- قبل الرفع Production غيّر SECRET_KEY و DEBUG و ALLOWED_HOSTS.
- يمكن لاحقاً إضافة API، تطبيق موبايل، PDF فعلي، ربط واتساب، وربط شركات توصيل.
