from django import forms
from django.utils import timezone
from .models import Customer, Product, DeliveryCompany, Order, Payment, FollowUp, CashTransaction, Expense, Task, Note, Attachment, InventoryMovement, ReturnRecord

class BaseArabicForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for _, field in self.fields.items():
            css='form-control'
            if isinstance(field.widget, forms.CheckboxInput): css='form-check-input'
            if isinstance(field.widget, forms.Select): css='form-select'
            field.widget.attrs.update({'class': css})

class CustomerForm(BaseArabicForm):
    class Meta:
        model=Customer; fields=['name','phone','secondary_phone','email','city','area','address','source','grade','tags','notes','next_action_date']
        widgets={'address':forms.Textarea(attrs={'rows':3}),'notes':forms.Textarea(attrs={'rows':3}),'next_action_date':forms.DateInput(attrs={'type':'date'})}
class ProductForm(BaseArabicForm):
    class Meta: model=Product; fields='__all__'
class DeliveryCompanyForm(BaseArabicForm):
    class Meta: model=DeliveryCompany; fields='__all__'
class OrderForm(BaseArabicForm):
    class Meta:
        model=Order; fields=['customer','product','quantity','unit_price','discount','delivery_company','delivery_fee','payment_method','status','payment_status','priority','delivery_tracking_number','due_date','assigned_to','notes']
        widgets={'notes':forms.Textarea(attrs={'rows':3}),'due_date':forms.DateInput(attrs={'type':'date'})}
class PaymentForm(BaseArabicForm):
    class Meta:
        model=Payment; fields=['order','cashbox','amount','method','payment_date','reference','notes']
        widgets={'payment_date':forms.DateTimeInput(attrs={'type':'datetime-local'}),'notes':forms.Textarea(attrs={'rows':3})}
class FollowUpForm(BaseArabicForm):
    class Meta:
        model=FollowUp; fields=['customer','order','result','note','next_followup_date','assigned_to']
        widgets={'next_followup_date':forms.DateInput(attrs={'type':'date'}),'note':forms.Textarea(attrs={'rows':4})}
class TaskForm(BaseArabicForm):
    class Meta:
        model=Task; fields=['title','description','customer','order','due_date','status','priority','assigned_to']
        widgets={'due_date':forms.DateInput(attrs={'type':'date'}),'description':forms.Textarea(attrs={'rows':3})}
class NoteForm(BaseArabicForm):
    class Meta:
        model=Note; fields=['customer','order','title','body']
        widgets={'body':forms.Textarea(attrs={'rows':4})}
class AttachmentForm(BaseArabicForm):
    class Meta: model=Attachment; fields=['customer','order','title','file']
class CashTransactionForm(BaseArabicForm):
    class Meta:
        model=CashTransaction; fields=['cashbox','transaction_type','amount','description','date']
        widgets={'date':forms.DateTimeInput(attrs={'type':'datetime-local'})}
class ExpenseForm(BaseArabicForm):
    class Meta:
        model=Expense; fields='__all__'
        widgets={'date':forms.DateTimeInput(attrs={'type':'datetime-local'})}

class InventoryMovementForm(BaseArabicForm):
    class Meta:
        model=InventoryMovement; fields=['product','order','movement_type','quantity','date','reference','notes']
        widgets={'date':forms.DateTimeInput(attrs={'type':'datetime-local'}),'notes':forms.Textarea(attrs={'rows':3})}

class ReturnRecordForm(BaseArabicForm):
    class Meta:
        model=ReturnRecord; fields=['order','product','quantity','reason','refund_amount','returned_to_stock','date','notes']
        widgets={'date':forms.DateTimeInput(attrs={'type':'datetime-local'}),'notes':forms.Textarea(attrs={'rows':3})}

class NewOrderForm(forms.Form):
    buyer_name=forms.CharField(label='اسم المشتري', max_length=160)
    buyer_phone=forms.CharField(label='رقم الهاتف', max_length=40)
    buyer_city=forms.CharField(label='المدينة', max_length=100, required=False)
    buyer_area=forms.CharField(label='المنطقة', max_length=100, required=False)
    buyer_address=forms.CharField(label='العنوان', required=False, widget=forms.Textarea(attrs={'rows':2}))
    product=forms.ModelChoiceField(label='المنتج من المستودع', queryset=Product.objects.filter(is_active=True), required=False)
    product_name=forms.CharField(label='أو اسم منتج جديد', max_length=160, required=False, help_text='استخدمه إذا المنتج غير موجود بالمستودع')
    sku=forms.CharField(label='رمز المنتج الجديد', max_length=50, required=False)
    quantity=forms.IntegerField(label='الكمية', min_value=1, initial=1)
    unit_price=forms.DecimalField(label='سعر الوحدة', max_digits=12, decimal_places=2)
    discount=forms.DecimalField(label='خصم', max_digits=12, decimal_places=2, initial=0, required=False)
    delivery_fee=forms.DecimalField(label='أجرة التوصيل/الإضافات', max_digits=12, decimal_places=2, initial=0, required=False)
    delivery_company=forms.ModelChoiceField(label='شركة التوصيل', queryset=DeliveryCompany.objects.filter(is_active=True), required=False)
    status=forms.ChoiceField(label='حالة الطلب', choices=Order.STATUS_CHOICES, initial='new')
    payment_method=forms.ChoiceField(label='طريقة الدفع / الذمة', choices=Order.PAYMENT_METHOD_CHOICES, initial='delivery')
    amount_paid=forms.DecimalField(label='المبلغ المدفوع الآن', max_digits=14, decimal_places=2, initial=0, required=False, help_text='اتركه صفر إذا المبلغ ذمة أو لم يتم التحصيل')
    notes=forms.CharField(label='ملاحظات', required=False, widget=forms.Textarea(attrs={'rows':3}))
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['product'].queryset=Product.objects.filter(is_active=True)
        self.fields['delivery_company'].queryset=DeliveryCompany.objects.filter(is_active=True)
        for _, field in self.fields.items():
            css='form-control'
            if isinstance(field.widget, forms.Select): css='form-select'
            field.widget.attrs.update({'class':css})
    def clean(self):
        cleaned=super().clean()
        if not cleaned.get('product') and not cleaned.get('product_name'):
            raise forms.ValidationError('اختر منتج من المستودع أو أدخل اسم منتج جديد.')
        if cleaned.get('product_name') and not cleaned.get('sku'):
            cleaned['sku']='AUTO-' + timezone.now().strftime('%Y%m%d%H%M%S')
        return cleaned
