from django.contrib.auth import get_user_model, login
from decimal import Decimal
from openpyxl import Workbook
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Customer, Product, DeliveryCompany, CashBox, Order, InventoryMovement, Payment, CashTransaction
from .forms import CustomerForm, ProductForm, DeliveryCompanyForm, CashBoxForm, InventoryInForm, NewOrderForm

@login_required
def dashboard(request):
    orders = Order.objects.all()
    products = Product.objects.all()
    context = {
        'orders_count': orders.count(),
        'today_orders': orders.filter(order_date__date__isnull=False).count(),
        'products_count': products.count(),
        'stock_qty': products.aggregate(s=Sum('stock_quantity'))['s'] or 0,
        'delivery_receivables': sum([o.remaining_amount for o in orders.filter(payment_method='delivery', delivery_company__isnull=False)], Decimal('0')),
        'customer_receivables': sum([o.remaining_amount for o in orders.filter(payment_method='unpaid')], Decimal('0')),
        'cash_total': sum([b.balance for b in CashBox.objects.all()], Decimal('0')),
        'recent_orders': orders.select_related('customer','product','delivery_company')[:8],
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def order_list(request):
    q = request.GET.get('q','').strip()
    status = request.GET.get('status','')
    payment = request.GET.get('payment','')
    orders = Order.objects.select_related('customer','product','delivery_company').prefetch_related('payments').all()
    if q:
        orders = orders.filter(Q(customer__name__icontains=q)|Q(customer__phone__icontains=q)|Q(product__name__icontains=q)|Q(notes__icontains=q))
    if status:
        orders = orders.filter(status=status)
    if payment:
        orders = orders.filter(payment_method=payment)
    return render(request, 'core/order_list.html', {'orders':orders,'q':q,'status':status,'payment':payment,'status_choices':Order.STATUS_CHOICES,'payment_choices':Order.PAYMENT_METHOD_CHOICES,'companies':DeliveryCompany.objects.filter(is_active=True)})

@login_required
def order_create(request):
    form = NewOrderForm(request.POST or None)
    if form.is_valid():
        data = form.cleaned_data
        customer, _ = Customer.objects.get_or_create(phone=data['buyer_phone'], defaults={'name':data['buyer_name'],'city':data.get('buyer_city') or '', 'area':data.get('buyer_area') or '', 'address':data.get('buyer_address') or ''})
        customer.name = data['buyer_name']
        customer.city = data.get('buyer_city') or customer.city
        customer.area = data.get('buyer_area') or customer.area
        customer.address = data.get('buyer_address') or customer.address
        customer.save()
        product = data.get('product')
        if not product:
            product = Product.objects.create(sku=data['sku'], name=data['product_name'], selling_price=data['unit_price'], stock_quantity=0, low_stock_alert=0)
        order = Order.objects.create(customer=customer, product=product, quantity=data['quantity'], unit_price=data['unit_price'], discount=data.get('discount') or 0, delivery_fee=data.get('delivery_fee') or 0, delivery_company=data.get('delivery_company'), notes=data.get('notes') or '')
        messages.success(request, 'تم إنشاء الأوردر. الحالة: جديد، طريقة الدفع: غير مدفوع.')
        return redirect('order_list')
    return render(request, 'core/form.html', {'form':form,'title':'طلب جديد'})

@require_POST
@login_required
def order_quick_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status = request.POST.get('status')
    payment_method = request.POST.get('payment_method')
    delivery_company_id = request.POST.get('delivery_company')
    if delivery_company_id:
        order.delivery_company_id = delivery_company_id
    if status:
        order.status = status
    if payment_method:
        order.payment_method = payment_method
    if order.payment_method == 'delivery' and not order.delivery_company_id:
        messages.error(request, 'اختار شركة توصيل قبل تحويل الطلب إلى ذمم شركة التوصيل.')
        return redirect('order_list')
    if order.status in ['with_delivery','delivered'] and not order.delivery_company_id:
        messages.error(request, 'اختار شركة توصيل قبل تحويل الطلب إلى التوصيل.')
        return redirect('order_list')
    order.save()
    order.apply_order_effects()
    messages.success(request, 'تم تحديث الأوردر وانعكست الحركة تلقائياً.')
    return redirect('order_list')

@login_required
def product_list(request):
    q = request.GET.get('q','').strip()
    products = Product.objects.all()
    if q:
        products = products.filter(Q(name__icontains=q)|Q(sku__icontains=q)|Q(category__icontains=q))
    return render(request, 'core/product_list.html', {'products':products,'q':q})

@login_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save(); messages.success(request,'تم حفظ المنتج'); return redirect('product_list')
    return render(request, 'core/form.html', {'form':form,'title':'إضافة منتج'})

@login_required
def delivery_list(request):
    return render(request, 'core/delivery_list.html', {'companies':DeliveryCompany.objects.all()})

@login_required
def delivery_create(request):
    form = DeliveryCompanyForm(request.POST or None)
    if form.is_valid():
        form.save(); messages.success(request,'تم حفظ شركة التوصيل'); return redirect('delivery_list')
    return render(request, 'core/form.html', {'form':form,'title':'إضافة شركة توصيل'})

@login_required
def inventory(request):
    products = Product.objects.all()
    movements = InventoryMovement.objects.select_related('product','order')[:100]
    return render(request, 'core/inventory.html', {'products':products,'movements':movements})

@login_required
def inventory_in(request):
    form = InventoryInForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.movement_type = 'in'
        obj.save()
        messages.success(request,'تم إدخال الكمية للمستودع')
        return redirect('inventory')
    return render(request, 'core/form.html', {'form':form,'title':'إدخال للمستودع'})

@login_required
def cashboxes(request):
    boxes = CashBox.objects.all()
    transactions = CashTransaction.objects.select_related('cashbox')[:100]
    return render(request, 'core/cashboxes.html', {'boxes':boxes,'transactions':transactions})

@login_required
def cashbox_create(request):
    form = CashBoxForm(request.POST or None)
    if form.is_valid():
        form.save(); messages.success(request,'تم حفظ الصندوق'); return redirect('cashboxes')
    return render(request, 'core/form.html', {'form':form,'title':'إضافة صندوق'})

@login_required
def receivables(request):
    delivery_orders = Order.objects.select_related('customer','product','delivery_company').filter(payment_method='delivery', delivery_company__isnull=False)
    customer_orders = Order.objects.select_related('customer','product').filter(payment_method='unpaid')
    companies = DeliveryCompany.objects.all()
    company_summary = []
    for c in companies:
        qs = delivery_orders.filter(delivery_company=c)
        total = sum([o.remaining_amount for o in qs], Decimal('0'))
        if total:
            company_summary.append({'company':c,'total':total,'count':qs.count()})
    return render(request, 'core/receivables.html', {'delivery_orders':delivery_orders,'customer_orders':customer_orders,'company_summary':company_summary})

@login_required
def reports(request):
    orders = Order.objects.select_related('customer','product','delivery_company').all()
    total_sales = sum([o.total_amount for o in orders], Decimal('0'))
    total_paid = sum([o.paid_amount for o in orders], Decimal('0'))
    delivery_due = sum([o.remaining_amount for o in orders.filter(payment_method='delivery')], Decimal('0'))
    customer_due = sum([o.remaining_amount for o in orders.filter(payment_method='unpaid')], Decimal('0'))
    return render(request, 'core/reports.html', locals())

def _xlsx(filename, headers, rows):
    wb = Workbook(); ws = wb.active; ws.title = 'Report'; ws.append(headers)
    for r in rows:
        ws.append(r)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

@login_required
def export_orders_xlsx(request):
    rows = []
    for o in Order.objects.select_related('customer','product','delivery_company').all():
        rows.append([o.id, o.order_date.strftime('%Y-%m-%d'), o.customer.name, o.customer.phone, o.product.name, o.quantity, float(o.total_amount), o.get_status_display(), o.get_payment_method_display(), o.delivery_company.name if o.delivery_company else '', float(o.paid_amount), float(o.remaining_amount)])
    return _xlsx('orders.xlsx', ['ID','Date','Customer','Phone','Product','Qty','Total','Status','Payment/Receivable','Delivery Company','Paid','Remaining'], rows)

@login_required
def export_inventory_xlsx(request):
    rows = [[p.sku,p.name,p.category,p.stock_quantity,p.stock_status,float(p.selling_price),float(p.cost_price)] for p in Product.objects.all()]
    return _xlsx('inventory.xlsx', ['SKU','Product','Category','Stock','Status','Selling Price','Cost'], rows)

@login_required
def export_receivables_xlsx(request):
    rows = []
    qs = Order.objects.select_related('customer','product','delivery_company').filter(payment_method__in=['unpaid','delivery'])
    for o in qs:
        if o.remaining_amount > 0:
            rows.append([o.id,o.customer.name,o.customer.phone,o.product.name,o.get_payment_method_display(),o.delivery_company.name if o.delivery_company else '',float(o.total_amount),float(o.paid_amount),float(o.remaining_amount),o.get_status_display()])
    return _xlsx('receivables.xlsx', ['Order','Customer','Phone','Product','Type','Delivery Company','Total','Paid','Remaining','Status'], rows)
def first_setup(request):
    User = get_user_model()
    error = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username:
            error = 'أدخل اسم المستخدم'
        elif password1 != password2:
            error = 'كلمتا المرور غير متطابقتين'
        elif len(password1) < 6:
            error = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'
        else:
            user, created = User.objects.get_or_create(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password1)
            user.save()

            login(request, user)
            return redirect('dashboard')

    return render(request, 'core/first_setup.html', {'error': error})
