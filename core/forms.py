from django import forms
from .models import Customer, Product, DeliveryCompany, Order, InventoryMovement, CashBox, Payment

class BaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

class CustomerForm(BaseForm):
    class Meta:
        model = Customer
        fields = ['name','phone','city','area','address','notes']

class ProductForm(BaseForm):
    class Meta:
        model = Product
        fields = ['sku','name','category','selling_price','cost_price','stock_quantity','low_stock_alert','is_active','notes']

class DeliveryCompanyForm(BaseForm):
    class Meta:
        model = DeliveryCompany
        fields = ['name','phone','default_fee','notes','is_active']

class CashBoxForm(BaseForm):
class Meta:
    model = CashBox
    fields = [
        'name',
        'opening_balance',
        'currency',
        'notes',
    ]
class InventoryInForm(BaseForm):
    class Meta:
        model = InventoryMovement
        fields = ['product','movement_type','quantity','notes']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['movement_type'].initial = 'in'

class NewOrderForm(forms.Form):
    buyer_name = forms.CharField(label='اسم المشتري', max_length=160, widget=forms.TextInput(attrs={'class':'form-control'}))
    buyer_phone = forms.CharField(label='رقم الهاتف', max_length=40, widget=forms.TextInput(attrs={'class':'form-control'}))
    buyer_city = forms.CharField(label='المدينة', required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    buyer_area = forms.CharField(label='المنطقة', required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    buyer_address = forms.CharField(label='العنوان', required=False, widget=forms.Textarea(attrs={'class':'form-control','rows':2}))
    product = forms.ModelChoiceField(label='منتج موجود', queryset=Product.objects.filter(is_active=True), required=False, widget=forms.Select(attrs={'class':'form-control'}))
    product_name = forms.CharField(label='اسم منتج جديد', required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    sku = forms.CharField(label='رمز منتج جديد', required=False, widget=forms.TextInput(attrs={'class':'form-control'}))
    quantity = forms.IntegerField(label='الكمية', min_value=1, initial=1, widget=forms.NumberInput(attrs={'class':'form-control'}))
    unit_price = forms.DecimalField(label='سعر الوحدة', max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={'class':'form-control'}))
    discount = forms.DecimalField(label='خصم', max_digits=12, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    delivery_fee = forms.DecimalField(label='أجرة التوصيل/إضافات', max_digits=12, decimal_places=2, initial=0, required=False, widget=forms.NumberInput(attrs={'class':'form-control'}))
    delivery_company = forms.ModelChoiceField(label='شركة التوصيل', queryset=DeliveryCompany.objects.filter(is_active=True), required=False, widget=forms.Select(attrs={'class':'form-control'}))
    notes = forms.CharField(label='ملاحظات', required=False, widget=forms.Textarea(attrs={'class':'form-control','rows':3}))
    def clean(self):
        data = super().clean()
        if not data.get('product') and (not data.get('product_name') or not data.get('sku')):
            raise forms.ValidationError('اختار منتج موجود أو أدخل اسم ورمز منتج جديد.')
        return data
