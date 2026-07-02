# Generated manually for clean OrderFlow
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='CashBox',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160, verbose_name='اسم الصندوق')),
                ('opening_balance', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='الرصيد الافتتاحي')),
                ('currency', models.CharField(default='JOD', max_length=10, verbose_name='العملة')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160, verbose_name='اسم العميل')),
                ('phone', models.CharField(db_index=True, max_length=40, verbose_name='رقم الهاتف')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='المدينة')),
                ('area', models.CharField(blank=True, max_length=100, verbose_name='المنطقة')),
                ('address', models.TextField(blank=True, verbose_name='العنوان')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-updated_at']},
        ),
        migrations.CreateModel(
            name='DeliveryCompany',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160, verbose_name='اسم شركة التوصيل')),
                ('phone', models.CharField(blank=True, max_length=40, verbose_name='هاتف الشركة')),
                ('default_fee', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='أجرة التوصيل الافتراضية')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(max_length=50, unique=True, verbose_name='رمز المنتج')),
                ('name', models.CharField(max_length=160, verbose_name='اسم المنتج')),
                ('category', models.CharField(blank=True, max_length=100, verbose_name='التصنيف')),
                ('selling_price', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='سعر البيع')),
                ('cost_price', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='التكلفة')),
                ('stock_quantity', models.IntegerField(default=0, verbose_name='كمية المخزون')),
                ('low_stock_alert', models.IntegerField(default=0, verbose_name='حد التنبيه')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='الكمية')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='سعر الوحدة')),
                ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='خصم')),
                ('delivery_fee', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='أجرة التوصيل/الإضافات')),
                ('status', models.CharField(choices=[('new', 'جديد'), ('confirmed', 'مؤكد'), ('preparing', 'قيد التجهيز'), ('with_delivery', 'تم تسليمه لشركة التوصيل'), ('delivered', 'تم التسليم للعميل'), ('returned', 'راجع'), ('cancelled', 'ملغي'), ('rejected', 'مرفوض'), ('closed', 'مغلق')], db_index=True, default='new', max_length=30, verbose_name='حالة الطلب')),
                ('payment_method', models.CharField(choices=[('unpaid', 'غير مدفوع'), ('cash', 'نقدي'), ('cliq', 'كليك'), ('bank', 'تحويل بنكي'), ('card', 'بطاقة/فيزا'), ('delivery', 'ذمم شركة التوصيل'), ('wallet', 'محفظة إلكترونية'), ('other', 'أخرى')], db_index=True, default='unpaid', max_length=30, verbose_name='طريقة الدفع/الذمة')),
                ('payment_status', models.CharField(choices=[('unpaid', 'غير مدفوع'), ('partial', 'مدفوع جزئياً'), ('paid', 'مدفوع بالكامل'), ('refunded', 'مسترد')], db_index=True, default='unpaid', max_length=30, verbose_name='حالة الدفع')),
                ('order_date', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='تاريخ الطلب')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='core.customer', verbose_name='العميل')),
                ('delivery_company', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.deliverycompany', verbose_name='شركة التوصيل')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='core.product', verbose_name='المنتج')),
            ],
            options={'ordering': ['-order_date']},
        ),
        migrations.CreateModel(
            name='InventoryMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(choices=[('in', 'إدخال'), ('out', 'خروج للتوصيل/بيع'), ('return', 'مرتجع'), ('adjust', 'تسوية')], max_length=20, verbose_name='نوع الحركة')),
                ('quantity', models.IntegerField(verbose_name='الكمية')),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='التاريخ')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inventory_movements', to='core.order', verbose_name='الأوردر')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_movements', to='core.product', verbose_name='المنتج')),
            ],
            options={'ordering': ['-date']},
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='المبلغ')),
                ('method', models.CharField(choices=[('unpaid', 'غير مدفوع'), ('cash', 'نقدي'), ('cliq', 'كليك'), ('bank', 'تحويل بنكي'), ('card', 'بطاقة/فيزا'), ('delivery', 'ذمم شركة التوصيل'), ('wallet', 'محفظة إلكترونية'), ('other', 'أخرى')], max_length=30, verbose_name='طريقة الدفع')),
                ('payment_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='تاريخ الدفع')),
                ('reference', models.CharField(blank=True, max_length=120, verbose_name='المرجع')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('cashbox', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='core.cashbox', verbose_name='الصندوق')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.order', verbose_name='الأوردر')),
            ],
            options={'ordering': ['-payment_date']},
        ),
        migrations.CreateModel(
            name='CashTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('in', 'قبض'), ('out', 'صرف')], max_length=10, verbose_name='نوع الحركة')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='المبلغ')),
                ('description', models.CharField(max_length=255, verbose_name='البيان')),
                ('date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='التاريخ')),
                ('cashbox', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='core.cashbox', verbose_name='الصندوق')),
                ('source_payment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.payment')),
            ],
            options={'ordering': ['-date']},
        ),
    ]
