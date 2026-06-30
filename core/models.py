from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone

class TimeStampedModel(models.Model):
    created_at=models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)
    updated_at=models.DateTimeField('آخر تعديل', auto_now=True)
    class Meta:
        abstract=True

class Product(TimeStampedModel):
    sku=models.CharField('رمز المنتج', max_length=50, unique=True)
    name=models.CharField('اسم المنتج', max_length=160)
    category=models.CharField('التصنيف', max_length=100, blank=True)
    selling_price=models.DecimalField('سعر البيع', max_digits=12, decimal_places=2)
    cost_price=models.DecimalField('تكلفة المنتج', max_digits=12, decimal_places=2, default=0)
    stock_quantity=models.PositiveIntegerField('الكمية الحالية', default=0)
    low_stock_alert=models.PositiveIntegerField('حد التنبيه', default=5)
    is_active=models.BooleanField('فعال', default=True)
    notes=models.TextField('ملاحظات', blank=True)
    class Meta:
        verbose_name='منتج'; verbose_name_plural='المنتجات'; ordering=['name']
    @property
    def stock_status(self):
        if self.stock_quantity <= 0: return 'نفد المخزون'
        if self.stock_quantity <= self.low_stock_alert: return 'منخفض'
        return 'متوفر'
    def __str__(self): return f'{self.name} ({self.sku})'

class Customer(TimeStampedModel):
    name=models.CharField('اسم العميل', max_length=160)
    phone=models.CharField('رقم الهاتف', max_length=40, db_index=True)
    secondary_phone=models.CharField('رقم إضافي', max_length=40, blank=True)
    city=models.CharField('المدينة', max_length=100, blank=True, db_index=True)
    area=models.CharField('المنطقة', max_length=100, blank=True)
    address=models.TextField('العنوان', blank=True)
    source=models.CharField('مصدر العميل', max_length=100, blank=True, help_text='Facebook / Instagram / Referral / Website')
    tags=models.CharField('وسوم', max_length=255, blank=True)
    notes=models.TextField('ملاحظات', blank=True)
    class Meta:
        verbose_name='عميل'; verbose_name_plural='العملاء'; ordering=['-created_at']
    def __str__(self): return f'{self.name} - {self.phone}'

class DeliveryCompany(TimeStampedModel):
    name=models.CharField('اسم شركة التوصيل', max_length=160)
    phone=models.CharField('هاتف الشركة', max_length=40, blank=True)
    default_fee=models.DecimalField('أجرة التوصيل الافتراضية', max_digits=12, decimal_places=2, default=0)
    tracking_url_template=models.CharField('رابط التتبع', max_length=255, blank=True, help_text='استخدم {tracking} داخل الرابط')
    notes=models.TextField('ملاحظات', blank=True)
    is_active=models.BooleanField('فعال', default=True)
    class Meta:
        verbose_name='شركة توصيل'; verbose_name_plural='شركات التوصيل'; ordering=['name']
    def __str__(self): return self.name

class CashBox(TimeStampedModel):
    name=models.CharField('اسم الصندوق', max_length=160)
    opening_balance=models.DecimalField('الرصيد الافتتاحي', max_digits=14, decimal_places=2, default=0)
    currency=models.CharField('العملة', max_length=10, default='JOD')
    notes=models.TextField('ملاحظات', blank=True)
    class Meta:
        verbose_name='صندوق نقد'; verbose_name_plural='الصناديق النقدية'
    def balance(self):
        incoming=self.transactions.filter(transaction_type='in').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        outgoing=self.transactions.filter(transaction_type='out').aggregate(total=Sum('amount'))['total'] or Decimal('0')
        return self.opening_balance + incoming - outgoing
    def __str__(self): return self.name

class Order(TimeStampedModel):
    STATUS_CHOICES=[('new','جديد'),('confirmed','مؤكد'),('preparing','قيد التجهيز'),('with_delivery','مع التوصيل'),('delivered','تم التسليم'),('cancelled','ملغي'),('returned','راجع')]
    PAYMENT_STATUS=[('unpaid','غير مدفوع'),('partial','مدفوع جزئياً'),('paid','مدفوع بالكامل'),('refunded','مسترد')]
    PRIORITY_CHOICES=[('normal','عادي'),('high','مهم'),('urgent','عاجل')]
    customer=models.ForeignKey(Customer, verbose_name='العميل', on_delete=models.PROTECT, related_name='orders')
    product=models.ForeignKey(Product, verbose_name='المنتج', on_delete=models.PROTECT, related_name='orders')
    quantity=models.PositiveIntegerField('الكمية', default=1)
    unit_price=models.DecimalField('سعر الوحدة', max_digits=12, decimal_places=2)
    discount=models.DecimalField('خصم', max_digits=12, decimal_places=2, default=0)
    delivery_company=models.ForeignKey(DeliveryCompany, verbose_name='شركة التوصيل', null=True, blank=True, on_delete=models.SET_NULL)
    delivery_fee=models.DecimalField('أجرة التوصيل', max_digits=12, decimal_places=2, default=0)
    status=models.CharField('حالة الطلب', max_length=30, choices=STATUS_CHOICES, default='new', db_index=True)
    payment_status=models.CharField('حالة الدفع', max_length=30, choices=PAYMENT_STATUS, default='unpaid', db_index=True)
    priority=models.CharField('الأولوية', max_length=20, choices=PRIORITY_CHOICES, default='normal')
    delivery_tracking_number=models.CharField('رقم التتبع', max_length=120, blank=True)
    order_date=models.DateTimeField('تاريخ الطلب', default=timezone.now, db_index=True)
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='الموظف المسؤول', null=True, blank=True, on_delete=models.SET_NULL)
    notes=models.TextField('ملاحظات', blank=True)
    class Meta:
        verbose_name='طلب'; verbose_name_plural='الطلبات'; ordering=['-order_date']; permissions=[('can_view_reports','Can view advanced reports')]
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
    def refresh_payment_status(self):
        paid=self.paid_amount
        if paid <= 0: self.payment_status='unpaid'
        elif paid < self.total_amount: self.payment_status='partial'
        else: self.payment_status='paid'
        self.save(update_fields=['payment_status','updated_at'])
    def tracking_url(self):
        if self.delivery_company and self.delivery_company.tracking_url_template and self.delivery_tracking_number:
            return self.delivery_company.tracking_url_template.replace('{tracking}', self.delivery_tracking_number)
        return ''
    def __str__(self): return f'طلب #{self.id} - {self.customer.name}'

class Payment(TimeStampedModel):
    METHOD_CHOICES=[('cash','نقدي'),('cliq','كليك'),('bank','تحويل بنكي'),('card','بطاقة'),('delivery','تحصيل من شركة التوصيل')]
    order=models.ForeignKey(Order, verbose_name='الطلب', related_name='payments', on_delete=models.CASCADE)
    cashbox=models.ForeignKey(CashBox, verbose_name='الصندوق', null=True, blank=True, on_delete=models.SET_NULL)
    amount=models.DecimalField('المبلغ', max_digits=14, decimal_places=2)
    method=models.CharField('طريقة الدفع', max_length=30, choices=METHOD_CHOICES, default='cash')
    payment_date=models.DateTimeField('تاريخ الدفع', default=timezone.now)
    reference=models.CharField('مرجع العملية', max_length=120, blank=True)
    notes=models.TextField('ملاحظات', blank=True)
    class Meta:
        verbose_name='دفعة'; verbose_name_plural='الدفعات'; ordering=['-payment_date']
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        self.order.refresh_payment_status()
        if self.cashbox:
            CashTransaction.objects.get_or_create(source_payment=self, defaults={'cashbox':self.cashbox,'transaction_type':'in','amount':self.amount,'description':f'تحصيل على طلب #{self.order.id}'})
    def __str__(self): return f'{self.amount} - طلب #{self.order.id}'

class CashTransaction(TimeStampedModel):
    TYPE_CHOICES=[('in','قبض'),('out','صرف')]
    cashbox=models.ForeignKey(CashBox, verbose_name='الصندوق', related_name='transactions', on_delete=models.CASCADE)
    transaction_type=models.CharField('نوع الحركة', max_length=10, choices=TYPE_CHOICES)
    amount=models.DecimalField('المبلغ', max_digits=14, decimal_places=2)
    description=models.CharField('البيان', max_length=255)
    date=models.DateTimeField('التاريخ', default=timezone.now)
    source_payment=models.OneToOneField(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        verbose_name='حركة صندوق'; verbose_name_plural='حركات الصناديق'; ordering=['-date']
    def __str__(self): return f'{self.get_transaction_type_display()} - {self.amount}'

class FollowUp(TimeStampedModel):
    RESULT_CHOICES=[('call_later','الاتصال لاحقاً'),('confirmed','تم التأكيد'),('no_answer','لا يوجد رد'),('cancelled','تم الإلغاء'),('complaint','شكوى'),('note','ملاحظة'),('upsell','فرصة بيع إضافية')]
    customer=models.ForeignKey(Customer, verbose_name='العميل', on_delete=models.CASCADE, related_name='followups')
    order=models.ForeignKey(Order, verbose_name='الطلب', null=True, blank=True, on_delete=models.SET_NULL, related_name='followups')
    result=models.CharField('نتيجة المتابعة', max_length=30, choices=RESULT_CHOICES)
    note=models.TextField('تفاصيل المتابعة')
    next_followup_date=models.DateField('موعد المتابعة القادمة', null=True, blank=True, db_index=True)
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='الموظف المسؤول', null=True, blank=True, on_delete=models.SET_NULL)
    class Meta:
        verbose_name='متابعة'; verbose_name_plural='المتابعات'; ordering=['next_followup_date','-created_at']
    def __str__(self): return f'{self.customer.name} - {self.get_result_display()}'

class Expense(TimeStampedModel):
    CATEGORY_CHOICES=[('ads','إعلانات'),('delivery','توصيل'),('salary','رواتب'),('rent','إيجار'),('supplies','مستلزمات'),('other','أخرى')]
    cashbox=models.ForeignKey(CashBox, verbose_name='الصندوق', null=True, blank=True, on_delete=models.SET_NULL)
    category=models.CharField('التصنيف', max_length=30, choices=CATEGORY_CHOICES)
    amount=models.DecimalField('المبلغ', max_digits=14, decimal_places=2)
    description=models.CharField('البيان', max_length=255)
    date=models.DateTimeField('التاريخ', default=timezone.now, db_index=True)
    class Meta:
        verbose_name='مصروف'; verbose_name_plural='المصاريف'; ordering=['-date']
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
    class Meta:
        verbose_name='سجل حركة'; verbose_name_plural='سجل الحركات'; ordering=['-created_at']
    def __str__(self): return self.action
