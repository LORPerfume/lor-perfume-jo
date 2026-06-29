from django import forms
from .models import Customer, Order, Payment, FollowUp, CashTransaction, Expense

class BaseArabicForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CustomerForm(BaseArabicForm):
    class Meta:
        model = Customer
        fields = '__all__'

class OrderForm(BaseArabicForm):
    class Meta:
        model = Order
        fields = '__all__'

class PaymentForm(BaseArabicForm):
    class Meta:
        model = Payment
        fields = '__all__'

class FollowUpForm(BaseArabicForm):
    class Meta:
        model = FollowUp
        fields = '__all__'
        widgets = {'next_followup_date': forms.DateInput(attrs={'type': 'date'})}

class CashTransactionForm(BaseArabicForm):
    class Meta:
        model = CashTransaction
        fields = ['cashbox', 'transaction_type', 'amount', 'description']

class ExpenseForm(BaseArabicForm):
    class Meta:
        model = Expense
        fields = '__all__'
