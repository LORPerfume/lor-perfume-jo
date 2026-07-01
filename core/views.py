import csv
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import *
from .forms import *

def log(request, action, model='', obj='', desc=''):
    if request.user.is_authenticated:
        ActivityLog.objects.create(user=request.user, action=action, model_name=model, object_id=str(obj), description=desc)

@login_required
def dashboard(request):
    today=timezone.localdate(); month_start=today.replace(day=1)
    orders=Order.objects.select_related('customer','product','delivery_company').all()
    todays_orders=orders.filter(order_date__date=today)
    total_orders=orders.count(); today_count=todays_orders.count(); pending=orders.exclude(status__in=['delivered','closed','cancelled','returned']).count()
    sales=sum([o.total_amount for o in orders], Decimal('0'))
    collected=Payment.objects.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    today_collected=Payment.objects.filter(payment_date__date=today).aggregate(s=Sum('amount'))['s'] or Decimal('0')
    expenses=Expense.objects.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    month_orders=orders.filter(order_date__date__gte=month_start)
    month_sales=sum([o.total_amount for o in month_orders], Decimal('0'))
    month_profit=sum([o.profit for o in month_orders], Decimal('0')) - (Expense.objects.filter(date__date__gte=month_start).aggregate(s=Sum('amount'))['s'] or Decimal('0'))
    receivables=sales-collected
    returned_today=orders.filter(status='returned', order_date__date=today).count()
    cashboxes=CashBox.objects.all()
    followups=FollowUp.objects.select_related('customer','order').filter(next_followup_date__isnull=False).order_by('next_followup_date')[:8]
    overdue_followups=FollowUp.objects.filter(next_followup_date__lt=today).count()
    overdue_tasks=Task.objects.filter(due_date__lt=today).exclude(status__in=['done','cancelled']).count()
    low_stock=Product.objects.filter(stock_quantity__lte=models.F('low_stock_alert'), is_active=True)[:8]
    tasks=Task.objects.select_related('customer').exclude(status__in=['done','cancelled']).order_by('due_date','-priority')[:8]
    recent_activity=ActivityLog.objects.select_related('user')[:10]
    top_products=Product.objects.annotate(total=Count('orders')).order_by('-total')[:5]
    sources=Customer.objects.values('source').annotate(total=Count('id')).order_by('-total')[:6]
    return render(request,'core/dashboard.html',locals())

@login_required
def global_search(request):
    q=request.GET.get('q','').strip()
    customers=Customer.objects.none(); orders=Order.objects.none(); tasks=Task.objects.none(); products=Product.objects.none(); followups=FollowUp.objects.none(); movements=InventoryMovement.objects.none()
    if q:
        customers=Customer.objects.filter(Q(name__icontains=q)|Q(phone__icontains=q)|Q(city__icontains=q)|Q(tags__icontains=q))[:20]
        orders=Order.objects.select_related('customer','product').filter(Q(customer__name__icontains=q)|Q(customer__phone__icontains=q)|Q(product__name__icontains=q)|Q(status__icontains=q)|Q(delivery_tracking_number__icontains=q))[:20]
        tasks=Task.objects.filter(Q(title__icontains=q)|Q(description__icontains=q))[:20]
        products=Product.objects.filter(Q(name__icontains=q)|Q(sku__icontains=q)|Q(category__icontains=q)|Q(notes__icontains=q))[:20]
        followups=FollowUp.objects.select_related('customer','order').filter(Q(customer__name__icontains=q)|Q(customer__phone__icontains=q)|Q(note__icontains=q)|Q(result__icontains=q))[:20]
        movements=InventoryMovement.objects.select_related('product','order').filter(Q(product__name__icontains=q)|Q(product__sku__icontains=q)|Q(reference__icontains=q)|Q(notes__icontains=q))[:20]
    return render(request,'core/search.html',locals())

def list_common(request, model, template, name, q_fields=(), extra_filter=None):
    q=request.GET.get('q','').strip(); qs=model.objects.all()
    if extra_filter: qs=extra_filter(qs)
    if q and q_fields:
        query=Q()
        for f in q_fields: query |= Q(**{f+'__icontains':q})
        qs=qs.filter(query)
    return render(request,template,{name:qs,'q':q})

@login_required
def customer_list(request): return list_common(request,Customer,'core/customer_list.html','customers',['name','phone','city','area','tags','source'])
@login_required
def customer_detail(request, pk):
    customer=get_object_or_404(Customer,pk=pk)
    timeline=[]
    for o in customer.orders.all(): timeline.append((o.created_at,'طلب/معاملة',f'#{o.id} - {o.product.name} - {o.get_status_display()}', reverse('order_detail',args=[o.id])))
    for f in customer.followups.all(): timeline.append((f.created_at,'متابعة',f'{f.get_result_display()} - {f.note[:80]}',''))
    for t in customer.tasks.all(): timeline.append((t.created_at,'مهمة',f'{t.title} - {t.get_status_display()}',''))
    for n in customer.quick_notes.all(): timeline.append((n.created_at,'ملاحظة',n.body[:120],''))
    timeline=sorted(timeline, key=lambda x:x[0], reverse=True)
    return render(request,'core/customer_detail.html',locals())
@login_required
def customer_create(request):
    form=CustomerForm(request.POST or None)
    if form.is_valid(): obj=form.save(); log(request,'إضافة عميل','Customer',obj.id,obj.name); messages.success(request,'تمت إضافة العميل'); return redirect('customer_detail',obj.id)
    return render(request,'core/form.html',{'form':form,'title':'إضافة عميل'})
@login_required
def customer_edit(request,pk):
    obj=get_object_or_404(Customer,pk=pk); form=CustomerForm(request.POST or None,instance=obj)
    if form.is_valid(): form.save(); log(request,'تعديل عميل','Customer',obj.id,obj.name); messages.success(request,'تم التعديل'); return redirect('customer_detail',obj.id)
    return render(request,'core/form.html',{'form':form,'title':'تعديل عميل'})

@login_required
def order_list(request):
    q=request.GET.get('q','').strip(); status=request.GET.get('status',''); payment=request.GET.get('payment',''); start=request.GET.get('start',''); end=request.GET.get('end','')
    orders=Order.objects.select_related('customer','product','delivery_company').prefetch_related('payments').all()
    if q: orders=orders.filter(Q(customer__name__icontains=q)|Q(customer__phone__icontains=q)|Q(product__name__icontains=q)|Q(delivery_tracking_number__icontains=q)|Q(notes__icontains=q))
    if status: orders=orders.filter(status=status)
    if payment: orders=orders.filter(payments__method=payment).distinct()
    if start: orders=orders.filter(order_date__date__gte=start)
    if end: orders=orders.filter(order_date__date__lte=end)
    status_choices=Order.STATUS_CHOICES; payment_choices=Payment.METHOD_CHOICES
    return render(request,'core/order_list.html',locals())
@login_required
def order_detail(request, pk):
    order=get_object_or_404(Order.objects.select_related('customer','product'),pk=pk)
    return render(request,'core/order_detail.html',locals())
@login_required
def order_create(request):
    form=OrderForm(request.POST or None)
    if form.is_valid(): obj=form.save(); log(request,'إضافة طلب','Order',obj.id); messages.success(request,'تم إنشاء الطلب'); return redirect('order_detail',obj.id)
    return render(request,'core/form.html',{'form':form,'title':'إضافة طلب/معاملة'})
@login_required
def order_edit(request,pk):
    obj=get_object_or_404(Order,pk=pk); form=OrderForm(request.POST or None,instance=obj)
    if form.is_valid(): form.save(); log(request,'تعديل طلب','Order',obj.id); messages.success(request,'تم التعديل'); return redirect('order_detail',obj.id)
    return render(request,'core/form.html',{'form':form,'title':'تعديل طلب/معاملة'})

@login_required
def simple_create(request, form_class, title, redirect_name):
    form=form_class(request.POST or None, request.FILES or None)
    if form.is_valid():
        obj=form.save(commit=False)
        if hasattr(obj,'created_by_id'): obj.created_by=request.user
        if hasattr(obj,'uploaded_by_id'): obj.uploaded_by=request.user
        obj.save(); log(request,'إضافة '+title,obj.__class__.__name__,obj.id); messages.success(request,'تم الحفظ'); return redirect(redirect_name)
    return render(request,'core/form.html',{'form':form,'title':title})

@login_required
def product_list(request): return list_common(request,Product,'core/product_list.html','products',['sku','name','category'])
@login_required
def product_create(request): return simple_create(request,ProductForm,'إضافة منتج/خدمة','product_list')
@login_required
def product_edit(request,pk):
    obj=get_object_or_404(Product,pk=pk); form=ProductForm(request.POST or None,instance=obj)
    if form.is_valid(): form.save(); messages.success(request,'تم التعديل'); return redirect('product_list')
    return render(request,'core/form.html',{'form':form,'title':'تعديل منتج/خدمة'})

@login_required
def inventory_list(request):
    q=request.GET.get('q','').strip(); mtype=request.GET.get('type','')
    products=Product.objects.all()
    movements=InventoryMovement.objects.select_related('product','order').all()
    returns=ReturnRecord.objects.select_related('order','product','order__customer').all()[:50]
    if q:
        products=products.filter(Q(name__icontains=q)|Q(sku__icontains=q)|Q(category__icontains=q))
        movements=movements.filter(Q(product__name__icontains=q)|Q(product__sku__icontains=q)|Q(reference__icontains=q)|Q(notes__icontains=q))
    if mtype: movements=movements.filter(movement_type=mtype)
    low_stock=products.filter(stock_quantity__lte=models.F('low_stock_alert'), is_active=True)
    return render(request,'core/inventory.html',locals())

@login_required
def inventory_movement_create(request): return simple_create(request,InventoryMovementForm,'إضافة حركة مستودع','inventory_list')
@login_required
def return_create(request): return simple_create(request,ReturnRecordForm,'تسجيل مرتجع','inventory_list')

@login_required
def delivery_statement(request):
    company_id=request.GET.get('company',''); start=request.GET.get('start',''); end=request.GET.get('end','')
    companies=DeliveryCompany.objects.filter(is_active=True)
    orders=Order.objects.select_related('customer','product','delivery_company').filter(delivery_company__isnull=False)
    if company_id: orders=orders.filter(delivery_company_id=company_id)
    if start: orders=orders.filter(order_date__date__gte=start)
    if end: orders=orders.filter(order_date__date__lte=end)
    delivered=orders.filter(status='delivered')
    total_due=sum([o.total_amount for o in delivered if o.payment_status!='paid'], Decimal('0'))
    total_delivery_fees=orders.aggregate(s=Sum('delivery_fee'))['s'] or Decimal('0')
    collected_by_delivery=Payment.objects.filter(method='delivery', order__in=orders).aggregate(s=Sum('amount'))['s'] or Decimal('0')
    net_with_delivery=sum([o.remaining_amount for o in orders if o.status in ['with_delivery','delivered']], Decimal('0'))
    return render(request,'core/delivery_statement.html',locals())

@login_required
def followup_list(request):
    today=timezone.localdate(); q=request.GET.get('q','').strip()
    followups=FollowUp.objects.select_related('customer','order').all()
    if q: followups=followups.filter(Q(customer__name__icontains=q)|Q(customer__phone__icontains=q)|Q(note__icontains=q))
    return render(request,'core/followup_list.html',locals())
@login_required
def followup_create(request): return simple_create(request,FollowUpForm,'إضافة متابعة','followup_list')

@login_required
def task_list(request):
    today=timezone.localdate(); status=request.GET.get('status','')
    tasks=Task.objects.select_related('customer','order').all()
    if status: tasks=tasks.filter(status=status)
    return render(request,'core/task_list.html',locals())
@login_required
def task_create(request): return simple_create(request,TaskForm,'إضافة مهمة','task_list')
@require_POST
@login_required
def task_done(request,pk):
    task=get_object_or_404(Task,pk=pk); task.status='done'; task.save(update_fields=['status','updated_at']); log(request,'إنجاز مهمة','Task',task.id); return redirect('task_list')

@login_required
def cashbox_list(request):
    cashboxes=CashBox.objects.all(); transactions=CashTransaction.objects.select_related('cashbox').all()[:80]
    by_method=Payment.objects.values('method').annotate(total=Sum('amount'), count=Count('id')).order_by('method')
    return render(request,'core/cashbox_list.html',locals())
@login_required
def cash_transaction_create(request): return simple_create(request,CashTransactionForm,'إضافة حركة صندوق','cashbox_list')
@login_required
def payment_create(request): return simple_create(request,PaymentForm,'إضافة دفعة','order_list')
@login_required
def expense_create(request): return simple_create(request,ExpenseForm,'إضافة مصروف','cashbox_list')

@login_required
def delivery_list(request): companies=DeliveryCompany.objects.all(); return render(request,'core/delivery_list.html',locals())
@login_required
def delivery_create(request): return simple_create(request,DeliveryCompanyForm,'إضافة شركة/شريك','delivery_list')
@login_required
def note_create(request): return simple_create(request,NoteForm,'إضافة ملاحظة','dashboard')
@login_required
def attachment_create(request): return simple_create(request,AttachmentForm,'رفع ملف','dashboard')

@login_required
def calendar_view(request):
    today=timezone.localdate()
    followups=FollowUp.objects.filter(next_followup_date__isnull=False).select_related('customer')
    tasks=Task.objects.filter(due_date__isnull=False).select_related('customer')
    orders=Order.objects.filter(due_date__isnull=False).select_related('customer')
    return render(request,'core/calendar.html',locals())

@login_required
def reports(request):
    start=request.GET.get('start',''); end=request.GET.get('end',''); status=request.GET.get('status','')
    orders=Order.objects.select_related('customer','product','delivery_company').all(); customers=Customer.objects.all()
    payments=Payment.objects.select_related('order').all(); returns=ReturnRecord.objects.select_related('order','product').all()
    if start:
        orders=orders.filter(order_date__date__gte=start); payments=payments.filter(payment_date__date__gte=start); returns=returns.filter(date__date__gte=start)
    if end:
        orders=orders.filter(order_date__date__lte=end); payments=payments.filter(payment_date__date__lte=end); returns=returns.filter(date__date__lte=end)
    if status: orders=orders.filter(status=status)
    by_status=orders.values('status').annotate(total=Count('id')).order_by('-total')
    by_city=customers.values('city').annotate(total=Count('id')).order_by('-total')[:10]
    by_source=customers.values('source').annotate(total=Count('id')).order_by('-total')[:10]
    top_products=Product.objects.annotate(total_orders=Count('orders')).order_by('-total_orders')[:10]
    total_sales=sum([o.total_amount for o in orders], Decimal('0'))
    collected=payments.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    receivables=sum([o.remaining_amount for o in orders], Decimal('0'))
    gross_profit=sum([o.profit for o in orders if o.status not in ['cancelled','returned','rejected']], Decimal('0'))
    expenses_total=Expense.objects.all()
    if start: expenses_total=expenses_total.filter(date__date__gte=start)
    if end: expenses_total=expenses_total.filter(date__date__lte=end)
    expenses_total=expenses_total.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    net_profit=gross_profit-expenses_total
    returned_qty=returns.aggregate(s=Sum('quantity'))['s'] or 0
    returned_amount=returns.aggregate(s=Sum('refund_amount'))['s'] or Decimal('0')
    inv_in=InventoryMovement.objects.filter(movement_type='in')
    inv_out=InventoryMovement.objects.filter(movement_type='out')
    if start:
        inv_in=inv_in.filter(date__date__gte=start); inv_out=inv_out.filter(date__date__gte=start)
    if end:
        inv_in=inv_in.filter(date__date__lte=end); inv_out=inv_out.filter(date__date__lte=end)
    inventory_in_qty=inv_in.aggregate(s=Sum('quantity'))['s'] or 0
    inventory_out_qty=inv_out.aggregate(s=Sum('quantity'))['s'] or 0
    payments_by_method=payments.values('method').annotate(total=Sum('amount'), count=Count('id')).order_by('method')
    status_choices=Order.STATUS_CHOICES
    return render(request,'core/reports.html',locals())

@login_required
def export_orders_csv(request):
    start=request.GET.get('start',''); end=request.GET.get('end',''); status=request.GET.get('status','')
    qs=Order.objects.select_related('customer','product','delivery_company')
    if start: qs=qs.filter(order_date__date__gte=start)
    if end: qs=qs.filter(order_date__date__lte=end)
    if status: qs=qs.filter(status=status)
    response=HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition']='attachment; filename="orders_report.csv"'
    writer=csv.writer(response); writer.writerow(['ID','Date','Customer','Phone','City','Product','Qty','Status','Payment Status','Payment Method(s)','Delivery Company','Tracking','Total','Paid','Remaining','Notes'])
    for o in qs:
        methods=' / '.join(sorted(set([p.get_method_display() for p in o.payments.all()])))
        writer.writerow([o.id,o.order_date.strftime('%Y-%m-%d'),o.customer.name,o.customer.phone,o.customer.city,o.product.name,o.quantity,o.get_status_display(),o.get_payment_status_display(),methods,o.delivery_company.name if o.delivery_company else '',o.delivery_tracking_number,o.total_amount,o.paid_amount,o.remaining_amount,o.notes])
    return response

@login_required
def export_inventory_csv(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition']='attachment; filename="inventory_report.csv"'
    writer=csv.writer(response); writer.writerow(['SKU','Product','Category','Current Stock','Low Stock Alert','Status','Selling Price','Cost Price'])
    for p in Product.objects.all(): writer.writerow([p.sku,p.name,p.category,p.stock_quantity,p.low_stock_alert,p.stock_status,p.selling_price,p.cost_price])
    return response
