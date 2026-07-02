from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.urls import reverse

class TimeStampedModel(models.Model):
    created_at=models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at=models.DateTimeField('آخر تعديل', auto_now=True)
    class Meta: abstract=True

class Customer(TimeStampedModel):
    GRADE=[('A','A - مهم جداً'),('B','B - جيد'),('C','C - عادي'),('D','D - ضعيف')]
    name=models.CharField('اسم العميل/الجهة', max_length=160)
    phone=models.CharField('رقم الهاتف', max_length=40, db_index=True)
    secondary_phone=models.CharField('رقم إضافي', max_length=40, blank=True)
    email=models.EmailField('البريد الإلكتروني', blank=True)
    city=models.CharField('المدينة', max_length=100, blank=True, db_index=True)
    area=models.CharField('المنطقة', max_length=100, blank=True)
    address=models.TextField('العنوان', blank=True)
    source=models.CharField('مصدر العميل', max_length=100, blank=True, help_text='Facebook / Instagram / Referral / Website / WhatsApp')
    grade=models.CharField('تصنيف العميل', max_length=5, choices=GRADE, default='B')
    tags=models.CharField('وسوم', max_length=255, blank=True)
    notes=models.TextField('ملاحظات', blank=True)
    last_contact_at=models.DateTimeField('آخر تواصل', null=True, blank=True)
    next_action_date=models.DateField('موعد الإجراء القادم', null=True, blank=True, db_index=True)
    class Meta: verbose_name='عميل'; verbose_name_plural='العملاء'; ordering=['-updated_at']
    def __str__(self): return f'{self.name} - {self.phone}'
    @property
    def whatsapp_url(self):
        digits=''.join(ch for ch in self.phone if ch.isdigit())
        if digits.startswith('0'): digits='962'+digits[1:]
        return f'https://wa.me/{digits}' if digits else ''
    @property
    def total_orders_amount(self): return sum([o.total_amount for o in self.orders.all()], Decimal('0'))
    @property
    def last_touch(self): return self.last_contact_at or self.updated_at
    def get_absolute_url(self): return reverse('customer_detail', args=[self.id])

class Product(TimeStampedModel):
    sku=models.CharField('رمز المنتج/الخدمة', max_length=50, unique=True)
    name=models.CharField('اسم المنتج/الخدمة', max_length=160)
    category=models.CharField('التصنيف', max_length=100, blank=True)
    selling_price=models.DecimalField('سعر البيع', max_digits=12, decimal_places=2)
    cost_price=models.DecimalField('التكلفة', max_digits=12, decimal_places=2, default=0)
    stock_quantity=models.PositiveIntegerField('الكمية الحالية', default=0)
    low_stock_alert=models.PositiveIntegerField('حد التنبيه', default=5)
    is_active=models.BooleanField('فعال', default=True)
    notes=models.TextField('ملاحظات', blank=True)
    class Meta: verbose_name='منتج/خدمة'; verbose_name_plural='المنتجات/الخدمات'; ordering=['name']
    @property
    def stock_status(self):
        if self.stock_quantity <= 0: return 'نفد المخزون'
        if self.stock_quantity <= self.low_stock_alert: return 'منخفض'
        return 'متوفر'
    def __str__(self): return f'{self.name} ({self.sku})'

class DeliveryCompany(TimeStampedModel):
    name=models.CharField('اسم شركة التوصيل/الشريك', max_length=160)
    phone=models.CharField('هاتف الشركة', max_length=40, blank=True)
    default_fee=models.DecimalField('الأجرة الافتراضية', max_digits=12, decimal_places=2, default=0)
    tracking_url_template=models.CharField('رابط التتبع', max_length=255, blank=True, help_text='استخدم {tracking} داخل الرابط')
    notes=models.TextField('ملاحظات', blank=True)
    is_active=models.BooleanField('فعال', default=True)
    class Meta: verbose_name='شركة/شريك'; verbose_name_plural='الشركات والشركاء'; ordering=['name']
    def __str__(self): return self.name

class CashBox(TimeStampedModel):
    name=models.CharField('اسم الصندوق', max_length=160)
    opening_balance=models.DecimalField('الرصيد الافتتاحي', max_digits=14, decimal_places=2, default=0)
    currency=models.CharField('العملة', max_length=10, default='JOD')
    notes=models.TextField('ملاحظات', blank=True)
    class Meta: verbose_name='صندوق نقد'; verbose_name_plural='الصناديق النقدية'
    def balance(self):
        incoming=self.transactions.filter(transaction_type='in').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        outgoing=self.transactions.filter(transaction_type='out').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return self.opening_balance + incoming - outgoing
    def __str__(self): return self.name

class Order(TimeStampedModel):
    STATUS_CHOICES=[('new','جديد'),('confirmed','مؤكد'),('preparing','قيد التجهيز'),('with_delivery','مع التوصيل'),('delivered','تم التسليم'),('cancelled','ملغي'),('rejected','مرفوض'),('no_answer','لم يتم الرد على الهاتف'),('returned','راجع'),('waiting','بانتظار رد'),('closed','مغلق')]
    PAYMENT_STATUS=[('unpaid','غير مدفوع'),('partial','مدفوع جزئياً'),('paid','مدفوع بالكامل'),('refunded','مسترد')]
    PRIORITY_CHOICES=[('low','منخفض'),('normal','عادي'),('high','مهم'),('urgent','عاجل')]
    customer=models.ForeignKey(Customer, verbose_name='العميل', on_delete=models.PROTECT, related_name='orders')
    product=models.ForeignKey(Product, verbose_name='المنتج/الخدمة', on_delete=models.PROTECT, related_name='orders')
    quantity=models.PositiveIntegerField('الكمية', default=1)
    unit_price=models.DecimalField('سعر الوحدة', max_digits=12, decimal_places=2)
    discount=models.DecimalField('خصم', max_digits=12, decimal_places=2, default=0)
    delivery_company=models.ForeignKey(DeliveryCompany, verbose_name='شركة/شريك', null=True, blank=True, on_delete=models.SET_NULL)
    delivery_fee=models.DecimalField('أجرة/تكلفة إضافية', max_digits=12, decimal_places=2, default=0)
    PAYMENT_METHOD_CHOICES=[('cash','نقدي'),('cliq','كليك'),('bank','تحويل بنكي'),('card','بطاقة/فيزا'),('delivery','ذمم شركة التوصيل'),('wallet','محفظة إلكترونية'),('other','أخرى')]
    payment_method=models.CharField('طريقة الدفع المتفق عليها', max_length=30, choices=PAYMENT_METHOD_CHOICES, default='delivery', db_index=True)
    status=models.CharField('حالة الطلب/المعاملة', max_length=30, choices=STATUS_CHOICES, default='new', db_index=True)
    payment_status=models.CharField('حالة الدفع', max_length=30, choices=PAYMENT_STATUS, default='unpaid', db_index=True)
    priority=models.CharField('الأولوية', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    delivery_tracking_number=models.CharField('رقم التتبع/المرجع', max_length=120, blank=True)
    order_date=models.DateTimeField('تاريخ الطلب/المعاملة', default=timezone.now, db_index=True)
    due_date=models.DateField('تاريخ الاستحقاق', null=True, blank=True, db_index=True)
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='المسؤول', null=True, blank=True, on_delete=models.SET_NULL)
    notes=models.TextField('ملاحظات', blank=True)
    class Meta: verbose_name='طلب/معاملة'; verbose_name_plural='الطلبات/المعاملات'; ordering=['-order_date']; permissions=[('can_view_reports','Can view advanced reports')]
    @property
    def subtotal(self): return self.quantity * self.unit_price
    @property
    def total_amount(self): return self.subtotal + self.delivery_fee - self.discount
    @property
    def paid_amount(self): return self.payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    @property
    def remaining_amount(self): return self.total_amount - self.paid_amount
    @property
    def profit(self): return (self.unit_price - self.product.cost_price) * self.quantity - self.discount
    @property
    def is_overdue(self): return bool(self.due_date and self.due_date < timezone.localdate() and self.status not in ['delivered','closed','cancelled'])
    def refresh_payment_status(self):
        paid=self.paid_amount
        self.payment_status='unpaid' if paid <= 0 else ('partial' if paid < self.total_amount else 'paid')
        self.save(update_fields=['payment_status','updated_at'])
    def tracking_url(self):
        if self.delivery_company and self.delivery_company.tracking_url_template and self.delivery_tracking_number:
            return self.delivery_company.tracking_url_template.replace('{tracking}', self.delivery_tracking_number)
        return ''
    def save(self,*args,**kwargs):
        old_status=None
        if self.pk:
            old_status=Order.objects.filter(pk=self.pk).values_list('status', flat=True).first()
        super().save(*args,**kwargs)
        if self.status=='delivered':
            InventoryMovement.objects.get_or_create(product=self.product, order=self, movement_type='out', reference=f'تسليم أوردر #{self.id}', defaults={'quantity':self.quantity,'date':timezone.now(),'notes':'خروج تلقائي عند تحويل حالة الأوردر إلى تم التسليم'})
    def __str__(self): return f'#{self.id} - {self.customer.name}'

class Payment(TimeStampedModel):
METHOD_CHOICES = [
    ('unpaid', 'غير مدفوع'),
    ('cash', 'نقدي'),
    ('click', 'كليك'),
    ('bank', 'تحويل بنكي'),
    ('visa', 'بطاقة/فيزا'),
    ('delivery', 'ذمم شركة التوصيل'),
    ('wallet', 'محفظة إلكترونية'),
    ('other', 'أخرى'),
]
order=models.ForeignKey(Order, verbose_name='الطلب/المعاملة', related_name='payments', on_delete=models.CASCADE)
    cashbox=models.ForeignKey(CashBox, verbose_name='الصندوق', null=True, blank=True, on_delete=models.SET_NULL)
    amount=models.DecimalField('المبلغ', max_digits=14, decimal_places=2)
    method=models.CharField('طريقة الدفع', max_length=30, choices=METHOD_CHOICES, default='cash')
    payment_date=models.DateTimeField('تاريخ الدفع', default=timezone.now)
    reference=models.CharField('مرجع العملية', max_length=120, blank=True)
    notes=models.TextField('ملاحظات', blank=True)
    class Meta: verbose_name='دفعة'; verbose_name_plural='الدفعات'; ordering=['-payment_date']
    def save(self,*args,**kwargs):
        if not self.cashbox_id:
            label=dict(self.METHOD_CHOICES).get(self.method, 'أخرى')
            box_name=f'صندوق {label}'
            self.cashbox, _ = CashBox.objects.get_or_create(name=box_name, defaults={'currency':'JOD','notes':'تم إنشاؤه تلقائياً حسب طريقة الدفع'})
        super().save(*args,**kwargs)
        self.order.refresh_payment_status()
        if self.cashbox:
            CashTransaction.objects.update_or_create(source_payment=self, defaults={'cashbox':self.cashbox,'transaction_type':'in','amount':self.amount,'description':f'تحصيل {self.get_method_display()} على أوردر #{self.order.id}','date':self.payment_date})
    def __str__(self): return f'{self.amount} - #{self.order.id}'

class CashTransaction(TimeStampedModel):
    TYPE_CHOICES=[('in','قبض'),('out','صرف')]
    cashbox=models.ForeignKey(CashBox, verbose_name='الصندوق', related_name='transactions', on_delete=models.CASCADE)
    transaction_type=models.CharField('نوع الحركة', max_length=10, choices=TYPE_CHOICES)
    amount=models.DecimalField('المبلغ', max_digits=14, decimal_places=2)
    description=models.CharField('البيان', max_length=255)
    date=models.DateTimeField('التاريخ', default=timezone.now)
    source_payment=models.OneToOneField(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta: verbose_name='حركة صندوق'; verbose_name_plural='حركات الصناديق'; ordering=['-date']
    def __str__(self): return f'{self.get_transaction_type_display()} - {self.amount}'

class FollowUp(TimeStampedModel):
    RESULT_CHOICES=[('call_later','الاتصال لاحقاً'),('confirmed','تم التأكيد'),('no_answer','لا يوجد رد'),('cancelled','تم الإلغاء'),('complaint','شكوى'),('note','ملاحظة'),('upsell','فرصة بيع إضافية'),('done','تم الإنجاز')]
    customer=models.ForeignKey(Customer, verbose_name='العميل', on_delete=models.CASCADE, related_name='followups')
    order=models.ForeignKey(Order, verbose_name='الطلب/المعاملة', null=True, blank=True, on_delete=models.SET_NULL, related_name='followups')
    result=models.CharField('نتيجة المتابعة', max_length=30, choices=RESULT_CHOICES)
    note=models.TextField('تفاصيل المتابعة')
    next_followup_date=models.DateField('موعد المتابعة القادمة', null=True, blank=True, db_index=True)
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='المسؤول', null=True, blank=True, on_delete=models.SET_NULL)
    class Meta: verbose_name='متابعة'; verbose_name_plural='المتابعات'; ordering=['next_followup_date','-created_at']
    @property
    def is_overdue(self): return bool(self.next_followup_date and self.next_followup_date < timezone.localdate())
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        Customer.objects.filter(pk=self.customer_id).update(last_contact_at=timezone.now(), next_action_date=self.next_followup_date)
    def __str__(self): return f'{self.customer.name} - {self.get_result_display()}'

class Task(TimeStampedModel):
    STATUS=[('todo','مطلوب'),('doing','قيد العمل'),('done','منجز'),('cancelled','ملغي')]
    PRIORITY=[('low','منخفض'),('normal','عادي'),('high','مهم'),('urgent','عاجل')]
    title=models.CharField('المهمة', max_length=180)
    description=models.TextField('التفاصيل', blank=True)
    customer=models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks', verbose_name='العميل')
    order=models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks', verbose_name='الطلب/المعاملة')
    due_date=models.DateField('تاريخ التنفيذ', null=True, blank=True, db_index=True)
    status=models.CharField('الحالة', max_length=20, choices=STATUS, default='todo', db_index=True)
    priority=models.CharField('الأولوية', max_length=20, choices=PRIORITY, default='normal')
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='المسؤول')
    class Meta: verbose_name='مهمة'; verbose_name_plural='المهام'; ordering=['status','due_date','-priority']
    @property
    def is_overdue(self): return bool(self.due_date and self.due_date < timezone.localdate() and self.status not in ['done','cancelled'])
    def __str__(self): return self.title

class Note(TimeStampedModel):
    customer=models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE, related_name='quick_notes', verbose_name='العميل')
    order=models.ForeignKey(Order, null=True, blank=True, on_delete=models.CASCADE, related_name='quick_notes', verbose_name='الطلب/المعاملة')
    title=models.CharField('العنوان', max_length=180, blank=True)
    body=models.TextField('الملاحظة')
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta: verbose_name='ملاحظة'; verbose_name_plural='الملاحظات'; ordering=['-created_at']
    def __str__(self): return self.title or self.body[:40]

class Attachment(TimeStampedModel):
    customer=models.ForeignKey(Customer, null=True, blank=True, on_delete=models.CASCADE, related_name='attachments', verbose_name='العميل')
    order=models.ForeignKey(Order, null=True, blank=True, on_delete=models.CASCADE, related_name='attachments', verbose_name='الطلب/المعاملة')
    file=models.FileField('الملف', upload_to='attachments/%Y/%m/')
    title=models.CharField('اسم الملف', max_length=180, blank=True)
    uploaded_by=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta: verbose_name='ملف مرفق'; verbose_name_plural='الملفات المرفقة'; ordering=['-created_at']

class Expense(TimeStampedModel):
    CATEGORY_CHOICES=[('ads','إعلانات'),('delivery','توصيل'),('salary','رواتب'),('rent','إيجار'),('supplies','مستلزمات'),('software','برمجيات'),('other','أخرى')]
    cashbox=models.ForeignKey(CashBox, verbose_name='الصندوق', null=True, blank=True, on_delete=models.SET_NULL)
    category=models.CharField('التصنيف', max_length=30, choices=CATEGORY_CHOICES)
    amount=models.DecimalField('المبلغ', max_digits=14, decimal_places=2)
    description=models.CharField('البيان', max_length=255)
    date=models.DateTimeField('التاريخ', default=timezone.now, db_index=True)
    class Meta: verbose_name='مصروف'; verbose_name_plural='المصاريف'; ordering=['-date']
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        if self.cashbox:
            CashTransaction.objects.get_or_create(cashbox=self.cashbox, transaction_type='out', amount=self.amount, description=f'مصروف: {self.description}')
    def __str__(self): return f'{self.get_category_display()} - {self.amount}'

class ActivityLog(TimeStampedModel):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action=models.CharField('الإجراء', max_length=120)
    model_name=models.CharField('الشاشة', max_length=120, blank=True)
    object_id=models.CharField('رقم السجل', max_length=120, blank=True)
    description=models.TextField('الوصف', blank=True)
    class Meta: verbose_name='سجل حركة'; verbose_name_plural='سجل الحركات'; ordering=['-created_at']
    def __str__(self): return self.action


class InventoryMovement(TimeStampedModel):
    MOVEMENT_TYPES=[
        ('in','إدخال للمستودع'),('out','تسليم/خروج'),('return','مرتجع'),
        ('adjust','تسوية جرد'),('damaged','تالف'),
    ]
    product=models.ForeignKey(Product, verbose_name='المادة/المنتج', related_name='inventory_movements', on_delete=models.CASCADE)
    order=models.ForeignKey(Order, verbose_name='الأوردر المرتبط', null=True, blank=True, related_name='inventory_movements', on_delete=models.SET_NULL)
    movement_type=models.CharField('نوع الحركة', max_length=20, choices=MOVEMENT_TYPES, db_index=True)
    quantity=models.IntegerField('الكمية')
    date=models.DateTimeField('تاريخ الحركة', default=timezone.now, db_index=True)
    reference=models.CharField('مرجع/رقم فاتورة', max_length=120, blank=True)
    notes=models.TextField('ملاحظات', blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='المستخدم')
    class Meta:
        verbose_name='حركة مستودع'; verbose_name_plural='حركات المستودع'; ordering=['-date']
    @property
    def signed_quantity(self):
        if self.movement_type in ['in','return']:
            return abs(self.quantity)
        if self.movement_type in ['out','damaged']:
            return -abs(self.quantity)
        return self.quantity
    def save(self,*args,**kwargs):
        is_new=self.pk is None
        old=0
        if not is_new:
            old=InventoryMovement.objects.get(pk=self.pk).signed_quantity
        super().save(*args,**kwargs)
        diff=self.signed_quantity-old
        Product.objects.filter(pk=self.product_id).update(stock_quantity=models.F('stock_quantity')+diff)
    def delete(self,*args,**kwargs):
        Product.objects.filter(pk=self.product_id).update(stock_quantity=models.F('stock_quantity')-self.signed_quantity)
        super().delete(*args,**kwargs)
    def __str__(self): return f'{self.product.name} - {self.get_movement_type_display()} - {self.quantity}'

class ReturnRecord(TimeStampedModel):
    REASONS=[('customer','رفض/إرجاع من العميل'),('damaged','تالف'),('wrong','منتج خاطئ'),('exchange','استبدال'),('other','أخرى')]
    order=models.ForeignKey(Order, verbose_name='الأوردر', related_name='returns', on_delete=models.CASCADE)
    product=models.ForeignKey(Product, verbose_name='المادة/المنتج', on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField('الكمية الراجعة', default=1)
    reason=models.CharField('سبب المرتجع', max_length=30, choices=REASONS, default='customer')
    refund_amount=models.DecimalField('مبلغ مسترد للعميل', max_digits=14, decimal_places=2, default=0)
    returned_to_stock=models.BooleanField('إرجاع للمستودع', default=True)
    date=models.DateTimeField('تاريخ المرتجع', default=timezone.now, db_index=True)
    notes=models.TextField('ملاحظات', blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='المستخدم')
    class Meta:
        verbose_name='مرتجع'; verbose_name_plural='المرتجعات'; ordering=['-date']
    def save(self,*args,**kwargs):
        is_new=self.pk is None
        super().save(*args,**kwargs)
        if is_new:
            self.order.status='returned'; self.order.save(update_fields=['status','updated_at'])
            if self.returned_to_stock:
                InventoryMovement.objects.create(product=self.product, order=self.order, movement_type='return', quantity=self.quantity, date=self.date, reference=f'مرتجع أوردر #{self.order_id}', notes=self.notes, created_by=self.created_by)
    def __str__(self): return f'مرتجع #{self.order_id} - {self.product.name}'
