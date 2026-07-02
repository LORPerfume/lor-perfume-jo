from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.utils import timezone

class Customer(models.Model):
    name = models.CharField('اسم العميل', max_length=160)
    phone = models.CharField('رقم الهاتف', max_length=40, db_index=True)
    city = models.CharField('المدينة', max_length=100, blank=True)
    area = models.CharField('المنطقة', max_length=100, blank=True)
    address = models.TextField('العنوان', blank=True)
    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-updated_at']
    def __str__(self):
        return f'{self.name} - {self.phone}'

class Product(models.Model):
    sku = models.CharField('رمز المنتج', max_length=50, unique=True)
    name = models.CharField('اسم المنتج', max_length=160)
    category = models.CharField('التصنيف', max_length=100, blank=True)
    selling_price = models.DecimalField('سعر البيع', max_digits=12, decimal_places=2, default=0)
    cost_price = models.DecimalField('التكلفة', max_digits=12, decimal_places=2, default=0)
    stock_quantity = models.IntegerField('كمية المخزون', default=0)
    low_stock_alert = models.IntegerField('حد التنبيه', default=0)
    is_active = models.BooleanField('فعال', default=True)
    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['name']
    @property
    def stock_status(self):
        if self.stock_quantity <= 0:
            return 'نفد المخزون'
        if self.stock_quantity <= self.low_stock_alert:
            return 'منخفض'
        return 'متوفر'
    def __str__(self):
        return f'{self.name} ({self.sku})'

class DeliveryCompany(models.Model):
    name = models.CharField('اسم شركة التوصيل', max_length=160)
    phone = models.CharField('هاتف الشركة', max_length=40, blank=True)
    default_fee = models.DecimalField('أجرة التوصيل الافتراضية', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('ملاحظات', blank=True)
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['name']
    def __str__(self):
        return self.name

class CashBox(models.Model):
    TYPE_CHOICES = [
        ('cash', 'نقدي'), ('cliq', 'كليك'), ('bank', 'بنك'), ('card', 'بطاقة/فيزا'), ('wallet', 'محفظة إلكترونية'), ('other', 'أخرى')
    ]
    name = models.CharField('اسم الصندوق', max_length=160)
    box_type = models.CharField('نوع الصندوق', max_length=30, choices=TYPE_CHOICES, default='cash', db_index=True)
    opening_balance = models.DecimalField('الرصيد الافتتاحي', max_digits=14, decimal_places=2, default=0)
    currency = models.CharField('العملة', max_length=10, default='JOD')
    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['name']
    @property
    def balance(self):
        incoming = self.transactions.filter(transaction_type='in').aggregate(s=Sum('amount'))['s'] or Decimal('0')
        outgoing = self.transactions.filter(transaction_type='out').aggregate(s=Sum('amount'))['s'] or Decimal('0')
        return self.opening_balance + incoming - outgoing
    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('new','جديد'), ('confirmed','مؤكد'), ('preparing','قيد التجهيز'),
        ('with_delivery','تم تسليمه لشركة التوصيل'), ('delivered','تم التسليم للعميل'),
        ('returned','راجع'), ('cancelled','ملغي'), ('rejected','مرفوض'), ('closed','مغلق')
    ]
    PAYMENT_METHOD_CHOICES = [
        ('unpaid','غير مدفوع'), ('cash','نقدي'), ('cliq','كليك'), ('bank','تحويل بنكي'),
        ('card','بطاقة/فيزا'), ('delivery','ذمم شركة التوصيل'), ('wallet','محفظة إلكترونية'), ('other','أخرى')
    ]
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders', verbose_name='العميل')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='orders', verbose_name='المنتج')
    quantity = models.PositiveIntegerField('الكمية', default=1)
    unit_price = models.DecimalField('سعر الوحدة', max_digits=12, decimal_places=2)
    discount = models.DecimalField('خصم', max_digits=12, decimal_places=2, default=0)
    delivery_fee = models.DecimalField('أجرة التوصيل/الإضافات', max_digits=12, decimal_places=2, default=0)
    delivery_company = models.ForeignKey(DeliveryCompany, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='شركة التوصيل')
    status = models.CharField('حالة الطلب', max_length=30, choices=STATUS_CHOICES, default='new', db_index=True)
    payment_method = models.CharField('طريقة الدفع/الذمة', max_length=30, choices=PAYMENT_METHOD_CHOICES, default='unpaid', db_index=True)
    order_date = models.DateTimeField('تاريخ الطلب', default=timezone.now, db_index=True)
    notes = models.TextField('ملاحظات', blank=True)
    stock_released = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-order_date']
    @property
    def subtotal(self):
        return self.quantity * self.unit_price
    @property
    def total_amount(self):
        return self.subtotal + self.delivery_fee - self.discount
    @property
    def paid_amount(self):
        return self.payments.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount
    @property
    def profit(self):
        return (self.unit_price - self.product.cost_price) * self.quantity - self.discount
    @property
    def receivable_type(self):
        if self.payment_method == 'delivery':
            return 'ذمة شركة التوصيل'
        if self.payment_method == 'unpaid':
            return 'ذمة العميل'
        return 'لا يوجد'
    def release_stock(self):
        if not self.stock_released:
            InventoryMovement.objects.create(order=self, product=self.product, movement_type='out', quantity=self.quantity, notes=f'خروج تلقائي من أوردر #{self.id}')
            self.stock_released = True
            Order.objects.filter(pk=self.pk).update(stock_released=True, updated_at=timezone.now())
    def return_stock(self):
        if self.stock_released:
            InventoryMovement.objects.create(order=self, product=self.product, movement_type='return', quantity=self.quantity, notes=f'رجوع تلقائي من أوردر #{self.id}')
            self.stock_released = False
            Order.objects.filter(pk=self.pk).update(stock_released=False, updated_at=timezone.now())
    def sync_auto_payment(self):
        self.payments.filter(is_auto=True).delete()
        paid_methods = ['cash','cliq','bank','card','wallet','other']
        if self.payment_method in paid_methods and self.total_amount > 0:
            Payment.objects.create(order=self, amount=self.total_amount, method=self.payment_method, is_auto=True, notes='دفعة تلقائية من صفحة الأوردرات اليومية')
    def apply_order_effects(self):
        if self.status in ['with_delivery','delivered']:
            self.release_stock()
        elif self.status in ['returned','cancelled','rejected']:
            self.return_stock()
        self.sync_auto_payment()
    def __str__(self):
        return f'#{self.id} - {self.customer.name}'

class InventoryMovement(models.Model):
    MOVEMENT_TYPES = [('in','إدخال'), ('out','خروج للتوصيل/بيع'), ('return','مرتجع'), ('adjust','تسوية')]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_movements', verbose_name='المنتج')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_movements', verbose_name='الأوردر')
    movement_type = models.CharField('نوع الحركة', max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField('الكمية')
    date = models.DateTimeField('التاريخ', default=timezone.now)
    notes = models.TextField('ملاحظات', blank=True)
    class Meta:
        ordering = ['-date']
    @property
    def signed_quantity(self):
        if self.movement_type in ['in','return']:
            return abs(self.quantity)
        if self.movement_type == 'out':
            return -abs(self.quantity)
        return self.quantity
    def save(self, *args, **kwargs):
        old = 0
        if self.pk:
            old = InventoryMovement.objects.get(pk=self.pk).signed_quantity
        super().save(*args, **kwargs)
        diff = self.signed_quantity - old
        Product.objects.filter(pk=self.product_id).update(stock_quantity=models.F('stock_quantity') + diff)
    def delete(self, *args, **kwargs):
        Product.objects.filter(pk=self.product_id).update(stock_quantity=models.F('stock_quantity') - self.signed_quantity)
        super().delete(*args, **kwargs)
    def __str__(self):
        return f'{self.product.name} - {self.get_movement_type_display()} - {self.quantity}'

class Payment(models.Model):
    METHOD_CHOICES = Order.PAYMENT_METHOD_CHOICES
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name='الأوردر')
    amount = models.DecimalField('المبلغ', max_digits=14, decimal_places=2)
    method = models.CharField('طريقة الدفع', max_length=30, choices=METHOD_CHOICES)
    cashbox = models.ForeignKey(CashBox, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments', verbose_name='الصندوق')
    payment_date = models.DateTimeField('تاريخ الدفع', default=timezone.now)
    reference = models.CharField('المرجع', max_length=120, blank=True)
    notes = models.TextField('ملاحظات', blank=True)
    is_auto = models.BooleanField(default=False, db_index=True)
    class Meta:
        ordering = ['-payment_date']
    def save(self, *args, **kwargs):
        if not self.cashbox_id and self.method not in ['unpaid','delivery']:
            label = dict(self.METHOD_CHOICES).get(self.method, 'أخرى')
            self.cashbox, _ = CashBox.objects.get_or_create(name=f'صندوق {label}', box_type=self.method if self.method in ['cash','cliq','bank','card','wallet'] else 'other')
        super().save(*args, **kwargs)
        if self.cashbox_id:
            CashTransaction.objects.update_or_create(source_payment=self, defaults={'cashbox':self.cashbox,'transaction_type':'in','amount':self.amount,'description':f'تحصيل أوردر #{self.order_id} - {self.get_method_display()}','date':self.payment_date})
    def delete(self, *args, **kwargs):
        CashTransaction.objects.filter(source_payment=self).delete()
        super().delete(*args, **kwargs)
    def __str__(self):
        return f'{self.amount} - {self.get_method_display()}'

class CashTransaction(models.Model):
    TYPE_CHOICES = [('in','قبض'), ('out','صرف')]
    cashbox = models.ForeignKey(CashBox, on_delete=models.CASCADE, related_name='transactions', verbose_name='الصندوق')
    transaction_type = models.CharField('نوع الحركة', max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField('المبلغ', max_digits=14, decimal_places=2)
    description = models.CharField('البيان', max_length=255)
    date = models.DateTimeField('التاريخ', default=timezone.now)
    source_payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        ordering = ['-date']
    def __str__(self):
        return f'{self.get_transaction_type_display()} - {self.amount}'
