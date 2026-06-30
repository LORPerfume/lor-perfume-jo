from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import Customer, Product, DeliveryCompany, Order, Payment, FollowUp, CashBox, Expense, CashTransaction, ActivityLog
from .forms import CustomerForm, ProductForm, DeliveryCompanyForm, OrderForm, PaymentForm, FollowUpForm, CashTransactionForm, ExpenseForm

def log(request, action, obj=None, description=''):
    ActivityLog.objects.create(user=request.user if request.user.is_authenticated else None, action=action, model_name=obj.__class__.__name__ if obj else '', object_id=getattr(obj,'id','') if obj else '', description=description)

@login_required
def dashboard(request):
    today=timezone.localdate(); month_start=today.replace(day=1)
    orders=Order.objects.select_related('customer','product','delivery_company')
    total_orders=orders.count(); delivered=orders.filter(status='delivered').count(); returned=orders.filter(status='returned').count()
    pending=orders.exclude(status__in=['delivered','cancelled','returned']).count()
    sales=sum([o.total_amount for o in orders]); receivables=sum([o.remaining_amount for o in orders.exclude(payment_status='paid')])
    collected=Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0'); expenses=Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    month_orders=orders.filter(order_date__date__gte=month_start); month_sales=sum([o.total_amount for o in month_orders]); month_profit=sum([o.profit for o in month_orders])
    low_stock=Product.objects.filter(stock_quantity__lte=5, is_active=True)[:8]
    latest_orders=orders[:12]
    followups=FollowUp.objects.filter(next_followup_date__isnull=False).select_related('customer','order').order_by('next_followup_date')[:10]
    status_data=list(orders.values('status').annotate(c=Count('id')).order_by('status'))
    return render(request,'core/dashboard.html',locals())

@login_required
def customer_list(request):
    q=request.GET.get('q',''); customers=Customer.objects.all()
    if q: customers=customers.filter(Q(name__icontains=q)|Q(phone__icontains=q)|Q(city__icontains=q)|Q(area__icontains=q)|Q(tags__icontains=q))
    return render(request,'core/customer_list.html',{'customers':customers,'q':q})
@login_required
def customer_create(request):
    form=CustomerForm(request.POST or None)
    if form.is_valid(): obj=form.save(); log(request,'إضافة عميل',obj); messages.success(request,'تم حفظ العميل بنجاح'); return redirect('customer_list')
    return render(request,'core/form.html',{'form':form,'title':'إضافة عميل','icon':'bi-person-plus'})
@login_required
def customer_edit(request,pk):
    obj=get_object_or_404(Customer,pk=pk); form=CustomerForm(request.POST or None,instance=obj)
    if form.is_valid(): obj=form.save(); log(request,'تعديل عميل',obj); messages.success(request,'تم تعديل العميل'); return redirect('customer_list')
    return render(request,'core/form.html',{'form':form,'title':'تعديل عميل','icon':'bi-pencil-square'})

@login_required
def product_list(request):
    q=request.GET.get('q',''); products=Product.objects.all()
    if q: products=products.filter(Q(name__icontains=q)|Q(sku__icontains=q)|Q(category__icontains=q))
    return render(request,'core/product_list.html',{'products':products,'q':q})
@login_required
def product_create(request):
    form=ProductForm(request.POST or None)
    if form.is_valid(): obj=form.save(); log(request,'إضافة منتج',obj); messages.success(request,'تم حفظ المنتج'); return redirect('product_list')
    return render(request,'core/form.html',{'form':form,'title':'إضافة منتج','icon':'bi-box-seam'})

@login_required
def delivery_list(request): return render(request,'core/delivery_list.html',{'companies':DeliveryCompany.objects.all()})
@login_required
def delivery_create(request):
    form=DeliveryCompanyForm(request.POST or None)
    if form.is_valid(): obj=form.save(); messages.success(request,'تم حفظ شركة التوصيل'); return redirect('delivery_list')
    return render(request,'core/form.html',{'form':form,'title':'إضافة شركة توصيل','icon':'bi-truck'})

@login_required
def order_list(request):
    q=request.GET.get('q',''); status=request.GET.get('status',''); pay=request.GET.get('pay','')
    orders=Order.objects.select_related('customer','product','delivery_company','assigned_to').all()
    if q: orders=orders.filter(Q(customer__name__icontains=q)|Q(customer__phone__icontains=q)|Q(product__name__icontains=q)|Q(delivery_tracking_number__icontains=q)|Q(id__icontains=q))
    if status: orders=orders.filter(status=status)
    if pay: orders=orders.filter(payment_status=pay)
    return render(request,'core/order_list.html',{'orders':orders,'q':q,'status':status,'pay':pay,'status_choices':Order.STATUS_CHOICES,'pay_choices':Order.PAYMENT_STATUS})
@login_required
def order_create(request):
    form=OrderForm(request.POST or None)
    if form.is_valid(): obj=form.save(); log(request,'إضافة طلب',obj); messages.success(request,'تم حفظ الطلب بنجاح'); return redirect('order_detail',pk=obj.pk)
    return render(request,'core/form.html',{'form':form,'title':'إضافة طلب','icon':'bi-cart-plus'})
@login_required
def order_edit(request,pk):
    obj=get_object_or_404(Order,pk=pk); form=OrderForm(request.POST or None,instance=obj)
    if form.is_valid(): obj=form.save(); log(request,'تعديل طلب',obj); messages.success(request,'تم تعديل الطلب'); return redirect('order_detail',pk=obj.pk)
    return render(request,'core/form.html',{'form':form,'title':f'تعديل طلب #{obj.id}','icon':'bi-pencil-square'})
@login_required
def order_detail(request,pk):
    order=get_object_or_404(Order.objects.select_related('customer','product','delivery_company'),pk=pk)
    return render(request,'core/order_detail.html',{'order':order})
@login_required
def invoice(request,pk):
    order=get_object_or_404(Order.objects.select_related('customer','product','delivery_company'),pk=pk)
    return render(request,'core/invoice.html',{'order':order})

@login_required
def payment_create(request):
    form=PaymentForm(request.POST or None)
    if form.is_valid(): obj=form.save(); log(request,'تسجيل دفعة',obj); messages.success(request,'تم تسجيل الدفعة بنجاح'); return redirect('order_detail',pk=obj.order.pk)
    return render(request,'core/form.html',{'form':form,'title':'تسجيل دفعة / تحصيل','icon':'bi-cash-coin'})
@login_required
def followup_list(request):
    today=timezone.localdate(); items=FollowUp.objects.select_related('customer','order','assigned_to').all()
    return render(request,'core/followup_list.html',{'items':items,'today':today})
@login_required
def followup_create(request):
    form=FollowUpForm(request.POST or None)
    if form.is_valid(): obj=form.save(); log(request,'إضافة متابعة',obj); messages.success(request,'تم تسجيل المتابعة'); return redirect('followup_list')
    return render(request,'core/form.html',{'form':form,'title':'إضافة متابعة','icon':'bi-telephone-outbound'})
@login_required
def cashbox_list(request): return render(request,'core/cashbox_list.html',{'cashboxes':CashBox.objects.all(),'transactions':CashTransaction.objects.select_related('cashbox')[:20]})
@login_required
def cash_transaction_create(request):
    form=CashTransactionForm(request.POST or None)
    if form.is_valid(): obj=form.save(commit=False); obj.created_by=request.user; obj.save(); messages.success(request,'تم تسجيل حركة الصندوق'); return redirect('cashbox_list')
    return render(request,'core/form.html',{'form':form,'title':'إضافة حركة صندوق','icon':'bi-wallet2'})
@login_required
def expense_create(request):
    form=ExpenseForm(request.POST or None)
    if form.is_valid(): obj=form.save(); log(request,'إضافة مصروف',obj); messages.success(request,'تم تسجيل المصروف'); return redirect('dashboard')
    return render(request,'core/form.html',{'form':form,'title':'إضافة مصروف','icon':'bi-receipt'})

@login_required
@permission_required('core.can_view_reports', raise_exception=False)
def reports(request):
    orders=Order.objects.select_related('customer','product')
    sales=sum([o.total_amount for o in orders]); profit=sum([o.profit for o in orders]); receivables=sum([o.remaining_amount for o in orders.exclude(payment_status='paid')])
    by_city=list(orders.values('customer__city').annotate(count=Count('id')).order_by('-count')[:10])
    by_product=list(orders.values('product__name').annotate(count=Count('id')).order_by('-count')[:10])
    return render(request,'core/reports.html',locals())
