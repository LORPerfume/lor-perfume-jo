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
    orders=Order.objects.select_related('customer','product').all()
    total_orders=orders.count(); pending=orders.exclude(status__in=['delivered','closed','cancelled']).count()
    sales=sum([o.total_amount for o in orders], Decimal('0'))
    collected=Payment.objects.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    expenses=Expense.objects.aggregate(s=Sum('amount'))['s'] or Decimal('0')
    month_orders=orders.filter(order_date__date__gte=month_start)
    month_sales=sum([o.total_amount for o in month_orders], Decimal('0'))
    month_profit=sum([o.profit for o in month_orders], Decimal('0')) - (Expense.objects.filter(date__date__gte=month_start).aggregate(s=Sum('amount'))['s'] or Decimal('0'))
    receivables=sales-collected
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
    customers=Customer.objects.none(); orders=Order.objects.none(); tasks=Task.objects.none()
    if q:
        customers=Customer.objects.filter(Q(name__icontains=q)|Q(phone__icontains=q)|Q(city__icontains=q)|Q(tags__icontains=q))[:20]
        orders=Order.objects.select_related('customer','product').filter(Q(customer__name__icontains=q)|Q(customer__phone__icontains=q)|Q(product__name__icontains=q)|Q(status__icontains=q)|Q(delivery_tracking_number__icontains=q))[:20]
        tasks=Task.objects.filter(Q(title__icontains=q)|Q(description__icontains=q))[:20]
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
    q=request.GET.get('q','').strip(); status=request.GET.get('status','')
    orders=Order.objects.select_related('customer','product','delivery_company').all()
    if q: orders=orders.filter(Q(customer__name__icontains=q)|Q(customer__phone__icontains=q)|Q(product__name__icontains=q)|Q(delivery_tracking_number__icontains=q))
    if status: orders=orders.filter(status=status)
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
    cashboxes=CashBox.objects.all(); transactions=CashTransaction.objects.select_related('cashbox').all()[:50]
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
    orders=Order.objects.select_related('customer','product').all(); customers=Customer.objects.all()
    by_status=orders.values('status').annotate(total=Count('id')).order_by('-total')
    by_city=customers.values('city').annotate(total=Count('id')).order_by('-total')[:10]
    by_source=customers.values('source').annotate(total=Count('id')).order_by('-total')[:10]
    top_products=Product.objects.annotate(total_orders=Count('orders')).order_by('-total_orders')[:10]
    return render(request,'core/reports.html',locals())

@login_required
def export_orders_csv(request):
    response=HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition']='attachment; filename="orders.csv"'
    writer=csv.writer(response); writer.writerow(['ID','Customer','Phone','Product','Status','Total','Paid','Remaining','Date'])
    for o in Order.objects.select_related('customer','product'):
        writer.writerow([o.id,o.customer.name,o.customer.phone,o.product.name,o.get_status_display(),o.total_amount,o.paid_amount,o.remaining_amount,o.order_date.strftime('%Y-%m-%d')])
    return response
