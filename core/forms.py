from django import forms
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
        model=Order; fields=['customer','product','quantity','unit_price','discount','delivery_company','delivery_fee','status','payment_status','priority','delivery_tracking_number','due_date','assigned_to','notes']
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
