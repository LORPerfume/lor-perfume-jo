from django.db import models
from django.utils import timezone
from decimal import Decimal

class Product(models.Model):
    name = models.CharField("اسم المنتج", max_length=120, default="المنتج الرئيسي")
    selling_price = models.DecimalField("سعر البيع", max_digits=10, decimal_places=2)
    cost_price = models.DecimalField("تكلفة المنتج", max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField("الكمية المتوفرة", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField("اسم العميل", max_length=120)
    phone = models.CharField("رقم الهاتف", max_length=30)
    city = models.CharField("المدينة", max_length=80, blank=True)
    area = models.CharField("المنطقة", max_length=80, blank=True)
    address = models.TextField("العنوان", blank=True)
    notes = models.TextField("ملاحظات", blank=True)
    created_at = models.DateTimeField("تاريخ الإدخال", auto_now_add=True)

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"

    def __str__(self):
        return f"{self.name} - {self.phone}"

class DeliveryCompany(models.Model):
    name = models.CharField("اسم شركة التوصيل", max_length=120)
    phone = models.CharField("هاتف الشركة", max_length=30, blank=True)
    default_fee = models.DecimalField("أجرة التوصيل الافتراضية", max_digits=10, decimal_places=2, default=0)
    notes = models.TextField("ملاحظات", blank=True)

    class Meta:
        verbose_name = "شركة توصيل"
        verbose_name_plural = "شركات التوصيل"

    def __str__(self):
        return self.name

class CashBox(models.Model):
    name = models.CharField("اسم الصندوق", max_length=120)
    opening_balance = models.DecimalField("الرصيد الافتتاحي", max_digits=12, decimal_places=2, default=0)
    notes = models.TextField("ملاحظات", blank=True)

    class Meta:
        verbose_name = "صندوق نقد"
        verbose_name_plural = "الصناديق النقدية"

    def balance(self):
        incoming = self.transactions.filter(transaction_type='in').aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
        outgoing = self.transactions.filter(transaction_type='out').aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
        return self.opening_balance + incoming - outgoing

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('confirmed', 'مؤكد'),
        ('with_delivery', 'مع شركة التوصيل'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
        ('returned', 'راجع'),
    ]
    PAYMENT_STATUS = [
        ('unpaid', 'غير مدفوع'),
        ('partial', 'مدفوع جزئياً'),
        ('paid', 'مدفوع بالكامل'),
    ]

    customer = models.ForeignKey(Customer, verbose_name="العميل", on_delete=models.PROTECT)
    product = models.ForeignKey(Product, verbose_name="المنتج", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField("الكمية", default=1)
    unit_price = models.DecimalField("سعر الوحدة", max_digits=10, decimal_places=2)
    discount = models.DecimalField("خصم", max_digits=10, decimal_places=2, default=0)
    delivery_company = models.ForeignKey(DeliveryCompany, verbose_name="شركة التوصيل", null=True, blank=True, on_delete=models.SET_NULL)
    delivery_fee = models.DecimalField("أجرة التوصيل", max_digits=10, decimal_places=2, default=0)
    status = models.CharField("حالة الطلب", max_length=30, choices=STATUS_CHOICES, default='new')
    payment_status = models.CharField("حالة الدفع", max_length=30, choices=PAYMENT_STATUS, default='unpaid')
    delivery_tracking_number = models.CharField("رقم التتبع", max_length=100, blank=True)
    order_date = models.DateTimeField("تاريخ الطلب", default=timezone.now)
    notes = models.TextField("ملاحظات", blank=True)

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ['-order_date']

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def total_amount(self):
        return self.subtotal + self.delivery_fee - self.discount

    @property
    def paid_amount(self):
        return self.payments.aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def profit(self):
        return (self.unit_price - self.product.cost_price) * self.quantity - self.discount

    def refresh_payment_status(self):
        if self.paid_amount <= 0:
            self.payment_status = 'unpaid'
        elif self.paid_amount < self.total_amount:
            self.payment_status = 'partial'
        else:
            self.payment_status = 'paid'
        self.save(update_fields=['payment_status'])

    def __str__(self):
        return f"طلب #{self.id} - {self.customer.name}"

class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'نقدي'),
        ('cliq', 'كليك'),
        ('bank', 'تحويل بنكي'),
        ('delivery', 'تحصيل من شركة التوصيل'),
    ]
    order = models.ForeignKey(Order, verbose_name="الطلب", related_name="payments", on_delete=models.CASCADE)
    cashbox = models.ForeignKey(CashBox, verbose_name="الصندوق", null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField("المبلغ", max_digits=12, decimal_places=2)
    method = models.CharField("طريقة الدفع", max_length=30, choices=METHOD_CHOICES, default='cash')
    payment_date = models.DateTimeField("تاريخ الدفع", default=timezone.now)
    notes = models.TextField("ملاحظات", blank=True)

    class Meta:
        verbose_name = "دفعة"
        verbose_name_plural = "الدفعات"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.refresh_payment_status()
        if self.cashbox:
            CashTransaction.objects.get_or_create(
                source_payment=self,
                defaults={
                    'cashbox': self.cashbox,
                    'transaction_type': 'in',
                    'amount': self.amount,
                    'description': f'تحصيل على طلب #{self.order.id}',
                }
            )

    def __str__(self):
        return f"{self.amount} - طلب #{self.order.id}"

class CashTransaction(models.Model):
    TYPE_CHOICES = [('in', 'قبض'), ('out', 'صرف')]
    cashbox = models.ForeignKey(CashBox, verbose_name="الصندوق", related_name="transactions", on_delete=models.CASCADE)
    transaction_type = models.CharField("نوع الحركة", max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField("المبلغ", max_digits=12, decimal_places=2)
    description = models.CharField("البيان", max_length=255)
    date = models.DateTimeField("التاريخ", default=timezone.now)
    source_payment = models.OneToOneField(Payment, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "حركة صندوق"
        verbose_name_plural = "حركات الصناديق"
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}"

class FollowUp(models.Model):
    RESULT_CHOICES = [
        ('call_later', 'الاتصال لاحقاً'),
        ('confirmed', 'تم التأكيد'),
        ('no_answer', 'لا يوجد رد'),
        ('cancelled', 'تم الإلغاء'),
        ('complaint', 'شكوى'),
        ('note', 'ملاحظة'),
    ]
    customer = models.ForeignKey(Customer, verbose_name="العميل", on_delete=models.CASCADE)
    order = models.ForeignKey(Order, verbose_name="الطلب", null=True, blank=True, on_delete=models.SET_NULL)
    result = models.CharField("نتيجة المتابعة", max_length=30, choices=RESULT_CHOICES)
    note = models.TextField("تفاصيل المتابعة")
    next_followup_date = models.DateField("موعد المتابعة القادمة", null=True, blank=True)
    created_at = models.DateTimeField("تاريخ المتابعة", auto_now_add=True)

    class Meta:
        verbose_name = "متابعة"
        verbose_name_plural = "المتابعات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} - {self.get_result_display()}"

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('ads', 'إعلانات'),
        ('delivery', 'توصيل'),
        ('salary', 'رواتب'),
        ('rent', 'إيجار'),
        ('other', 'أخرى'),
    ]
    cashbox = models.ForeignKey(CashBox, verbose_name="الصندوق", null=True, blank=True, on_delete=models.SET_NULL)
    category = models.CharField("التصنيف", max_length=30, choices=CATEGORY_CHOICES)
    amount = models.DecimalField("المبلغ", max_digits=12, decimal_places=2)
    description = models.CharField("البيان", max_length=255)
    date = models.DateTimeField("التاريخ", default=timezone.now)

    class Meta:
        verbose_name = "مصروف"
        verbose_name_plural = "المصاريف"
        ordering = ['-date']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.cashbox:
            CashTransaction.objects.get_or_create(
                cashbox=self.cashbox,
                transaction_type='out',
                amount=self.amount,
                description=f'مصروف: {self.description}',
            )

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount}"
