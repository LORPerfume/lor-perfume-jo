from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.contrib import messages
from decimal import Decimal
from .models import Customer, Order, Payment, FollowUp, CashBox, Expense
from .forms import CustomerForm, OrderForm, PaymentForm, FollowUpForm, CashTransactionForm, ExpenseForm

@login_required
def dashboard(request):
    total_orders = Order.objects.count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    pending_orders = Order.objects.exclude(status__in=['delivered', 'cancelled', 'returned']).count()
    receivables = sum([o.remaining_amount for o in Order.objects.exclude(payment_status='paid')])
    sales = sum([o.total_amount for o in Order.objects.all()])
    collected = Payment.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    cashboxes = CashBox.objects.all()
    latest_orders = Order.objects.select_related('customer', 'delivery_company')[:10]
    followups = FollowUp.objects.filter(next_followup_date__isnull=False).order_by('next_followup_date')[:10]

    return render(request, 'core/dashboard.html', {
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'pending_orders': pending_orders,
        'receivables': receivables,
        'sales': sales,
        'collected': collected,
        'expenses': expenses,
        'cashboxes': cashboxes,
        'latest_orders': latest_orders,
        'followups': followups,
    })

@login_required
def customer_list(request):
    q = request.GET.get('q', '')
    customers = Customer.objects.all().order_by('-created_at')
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q) | Q(city__icontains=q))
    return render(request, 'core/customer_list.html', {'customers': customers, 'q': q})

@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ العميل بنجاح')
        return redirect('customer_list')
    return render(request, 'core/form.html', {'form': form, 'title': 'إضافة عميل'})

@login_required
def order_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    orders = Order.objects.select_related('customer', 'delivery_company', 'product').all()
    if q:
        orders = orders.filter(Q(customer__name__icontains=q) | Q(customer__phone__icontains=q) | Q(delivery_tracking_number__icontains=q))
    if status:
        orders = orders.filter(status=status)
    return render(request, 'core/order_list.html', {'orders': orders, 'q': q, 'status': status})

@login_required
def order_create(request):
    form = OrderForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ الطلب بنجاح')
        return redirect('order_list')
    return render(request, 'core/form.html', {'form': form, 'title': 'إضافة طلب'})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'core/order_detail.html', {'order': order})

@login_required
def payment_create(request):
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم تسجيل الدفعة بنجاح')
        return redirect('order_list')
    return render(request, 'core/form.html', {'form': form, 'title': 'تسجيل دفعة / تحصيل'})

@login_required
def followup_create(request):
    form = FollowUpForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم تسجيل المتابعة بنجاح')
        return redirect('dashboard')
    return render(request, 'core/form.html', {'form': form, 'title': 'إضافة متابعة'})

@login_required
def cashbox_list(request):
    cashboxes = CashBox.objects.all()
    return render(request, 'core/cashbox_list.html', {'cashboxes': cashboxes})

@login_required
def cash_transaction_create(request):
    form = CashTransactionForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم تسجيل حركة الصندوق')
        return redirect('cashbox_list')
    return render(request, 'core/form.html', {'form': form, 'title': 'إضافة حركة صندوق'})

@login_required
def expense_create(request):
    form = ExpenseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم تسجيل المصروف')
        return redirect('dashboard')
    return render(request, 'core/form.html', {'form': form, 'title': 'إضافة مصروف'})
