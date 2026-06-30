from django import forms
from .models import Customer, Product, DeliveryCompany, Order, Payment, FollowUp, CashTransaction, Expense

class BaseArabicForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for name, field in self.fields.items():
            css='form-control'
            if isinstance(field.widget, forms.CheckboxInput): css='form-check-input'
            field.widget.attrs.update({'class': css})

class CustomerForm(BaseArabicForm):
    class Meta:
        model=Customer; fields=['name','phone','secondary_phone','city','area','address','source','tags','notes']
        widgets={'address':forms.Textarea(attrs={'rows':3}),'notes':forms.Textarea(attrs={'rows':3})}
class ProductForm(BaseArabicForm):
    class Meta:
        model=Product; fields='__all__'
class DeliveryCompanyForm(BaseArabicForm):
    class Meta:
        model=DeliveryCompany; fields='__all__'
class OrderForm(BaseArabicForm):
    class Meta:
        model=Order; fields=['customer','product','quantity','unit_price','discount','delivery_company','delivery_fee','status','priority','delivery_tracking_number','assigned_to','notes']
        widgets={'notes':forms.Textarea(attrs={'rows':3})}
class PaymentForm(BaseArabicForm):
    class Meta:
        model=Payment; fields=['order','cashbox','amount','method','payment_date','reference','notes']
        widgets={'payment_date':forms.DateTimeInput(attrs={'type':'datetime-local'}),'notes':forms.Textarea(attrs={'rows':3})}
class FollowUpForm(BaseArabicForm):
    class Meta:
        model=FollowUp; fields=['customer','order','result','note','next_followup_date','assigned_to']
        widgets={'next_followup_date':forms.DateInput(attrs={'type':'date'}),'note':forms.Textarea(attrs={'rows':4})}
class CashTransactionForm(BaseArabicForm):
    class Meta:
        model=CashTransaction; fields=['cashbox','transaction_type','amount','description','date']
        widgets={'date':forms.DateTimeInput(attrs={'type':'datetime-local'})}
class ExpenseForm(BaseArabicForm):
    class Meta:
        model=Expense; fields='__all__'
        widgets={'date':forms.DateTimeInput(attrs={'type':'datetime-local'})}
