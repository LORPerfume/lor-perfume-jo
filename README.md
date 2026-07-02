# OrderFlow - نسخة نظيفة بدون بيانات تجريبية

هذه النسخة لا تحتوي على أي منتجات أو أوردرات أو حركات مستودع أو مرتجعات أو عملاء تجريبيين.

مهم: إذا كنت ناشر المشروع على نفس قاعدة بيانات قديمة، لازم تعمل redeploy بعد رفع هذه النسخة حتى تعمل migration رقم 0006 وتحذف بيانات الديمو المعروفة مثل: lor perfume / SKU 001 / PKG-002 / SRV-001.

## التشغيل المحلي
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## التأكد من عدم وجود داتا تجريبية
```bash
python manage.py check_no_demo_data
```

## ملاحظات
- الصناديق لا تُنشأ كحركات مالية تجريبية.
- عند أول دفعة فعلية، يتم إنشاء صندوق طريقة الدفع تلقائياً إذا لم يكن موجوداً.
- لا يوجد أي seed أو demoData أو sampleData يتم تشغيله تلقائياً.
