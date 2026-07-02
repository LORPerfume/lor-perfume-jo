from django import forms
from .models import Customer, Product, DeliveryCompany, CashBox, InventoryMovement, Order


class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class CustomerForm(BaseForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'city', 'area', 'address', 'notes']


class ProductForm(BaseForm):
    class Meta:
        model = Product
        fields = [
            'sku',
            'name',
            'category',
            'selling_price',
            'cost_price',
            'stock_quantity',
            'low_stock_alert',
            'is_active',
            'notes',
        ]


class DeliveryCompanyForm(BaseForm):
    class Meta:
        model = DeliveryCompany
        fields = ['name', 'phone', 'default_fee', 'notes', 'is_active']


class CashBoxForm(BaseForm):
    class Meta:
        model = CashBox
        fields = ['name', 'opening_balance', 'currency', 'notes']


class InventoryInForm(BaseForm):
    class Meta:
        model = InventoryMovement
        fields = ['product', 'quantity', 'notes']

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.movement_type = 'in'
        if commit:
            obj.save()
        return obj


class NewOrderForm(forms.Form):
    buyer_name = forms.CharField(label='اسم المشتري', max_length=160)
    buyer_phone = forms.CharField(label='رقم الهاتف', max_length=40)
    buyer_city = forms.CharField(label='المدينة', max_length=100, required=False)
    buyer_area = forms.CharField(label='المنطقة', max_length=100, required=False)
    buyer_address = forms.CharField(label='العنوان', widget=forms.Textarea, required=False)

    product = forms.ModelChoiceField(
        label='المنتج',
        queryset=Product.objects.filter(is_active=True),
        required=True
    )

    quantity = forms.IntegerField(label='الكمية', min_value=1, initial=1)
    unit_price = forms.DecimalField(label='سعر الوحدة', max_digits=12, decimal_places=2)
    discount = forms.DecimalField(label='خصم', max_digits=12, decimal_places=2, initial=0, required=False)
    delivery_fee = forms.DecimalField(label='أجرة التوصيل/الإضافات', max_digits=12, decimal_places=2, initial=0, required=False)

    delivery_company = forms.ModelChoiceField(
        label='شركة التوصيل',
        queryset=DeliveryCompany.objects.filter(is_active=True),
        required=False
    )

    status = forms.ChoiceField(label='حالة الطلب', choices=Order.STATUS_CHOICES, initial='new')
    payment_method = forms.ChoiceField(label='طريقة الدفع/الذمة', choices=Order.PAYMENT_METHOD_CHOICES, initial='unpaid')
    notes = forms.CharField(label='ملاحظات', widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
