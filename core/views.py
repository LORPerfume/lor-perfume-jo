from decimal import Decimal
from openpyxl import Workbook
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .forms import CustomerForm, ProductForm, DeliveryCompanyForm, CashBoxForm, InventoryInForm, NewOrderForm
from .models import Customer, Product, DeliveryCompany, CashBox, Order, InventoryMovement


def first_setup(request):
    User = get_user_model()
    error = ''
    if User.objects.filter(is_superuser=True).exists() and not request.user.is_authenticated:
        return redirect('login')
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
            user, _ = User.objects.get_or_create(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password1)
            user.save()
            login(request, user)
            return redirect('dashboard')
    return render(request, 'core/first_setup.html', {'error': error})


def require_setup(view_func):
    def wrapper(request, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists() and request.path != '/setup/':
            return redirect('first_setup')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@require_setup
def dashboard(request):
    orders = Order.objects.select_related('customer', 'product', 'delivery_company').all()[:10]
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    inventory_qty = Product.objects.aggregate(s=Sum('stock_quantity'))['s'] or 0
    delivery_receivables = sum([o.remaining_amount for o in Order.objects.filter(payment_method='delivery')], Decimal('0'))
    customer_receivables = sum([o.remaining_amount for o in Order.objects.filter(payment_method='unpaid')], Decimal('0'))
    cash_total = sum([c.balance for c in CashBox.objects.all()], Decimal('0'))
    return render(request, 'core/dashboard.html', locals())


@login_required
@require_setup
def order_list(request):
    q = request.GET.get('q', '').strip()
    orders = Order.objects.select_related('customer', 'product', 'delivery_company').prefetch_related('payments').all()
    if q:
        orders = orders.filter(customer__name__icontains=q) | orders.filter(customer__phone__icontains=q) | orders.filter(product__name__icontains=q)
    status_choices = Order.STATUS_CHOICES
    payment_choices = Order.PAYMENT_METHOD_CHOICES
    return render(request, 'core/order_list.html', locals())


@login_required
@require_setup
def order_create(request):
    form = NewOrderForm(request.POST or None)
    if form.is_valid():
        d = form.cleaned_data
        customer, _ = Customer.objects.get_or_create(
            phone=d['buyer_phone'],
            defaults={'name': d['buyer_name'], 'city': d.get('buyer_city') or '', 'area': d.get('buyer_area') or '', 'address': d.get('buyer_address') or ''}
        )
        customer.name = d['buyer_name']
        customer.city = d.get('buyer_city') or customer.city
        customer.area = d.get('buyer_area') or customer.area
        customer.address = d.get('buyer_address') or customer.address
        customer.save()
        order = Order.objects.create(
            customer=customer,
            product=d['product'],
            quantity=d['quantity'],
            unit_price=d['unit_price'],
            discount=d.get('discount') or Decimal('0'),
            delivery_fee=d.get('delivery_fee') or Decimal('0'),
            delivery_company=d.get('delivery_company'),
            status=d['status'],
            payment_method=d['payment_method'],
            notes=d.get('notes') or '',
        )
        order.apply_order_effects()
        messages.success(request, 'تم إنشاء الأوردر')
        return redirect('order_list')
    return render(request, 'core/form.html', {'form': form, 'title': 'طلب جديد'})


@require_POST
@login_required
@require_setup
def order_quick_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.status = request.POST.get('status', order.status)
    order.payment_method = request.POST.get('payment_method', order.payment_method)
    if order.payment_method == 'delivery' and not order.delivery_company:
        messages.error(request, 'اختر شركة توصيل قبل تحويل الأوردر إلى ذمم شركة التوصيل')
        return redirect('order_list')
    order.save()
    order.apply_order_effects()
    messages.success(request, 'تم تحديث الأوردر وعكس الحركات تلقائياً')
    return redirect('order_list')


@login_required
@require_setup
def product_list(request):
    products = Product.objects.all()
    return render(request, 'core/product_list.html', locals())


@login_required
@require_setup
def product_create(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ المنتج')
        return redirect('product_list')
    return render(request, 'core/form.html', {'form': form, 'title': 'منتج جديد'})


@login_required
@require_setup
def inventory(request):
    products = Product.objects.all()
    movements = InventoryMovement.objects.select_related('product', 'order')[:100]
    return render(request, 'core/inventory.html', locals())


@login_required
@require_setup
def inventory_in(request):
    form = InventoryInForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم إدخال المخزون')
        return redirect('inventory')
    return render(request, 'core/form.html', {'form': form, 'title': 'إدخال مخزون'})


@login_required
@require_setup
def cashboxes(request):
    boxes = CashBox.objects.all()
    return render(request, 'core/cashboxes.html', locals())


@login_required
@require_setup
def cashbox_create(request):
    form = CashBoxForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ الصندوق')
        return redirect('cashboxes')
    return render(request, 'core/form.html', {'form': form, 'title': 'صندوق جديد'})


@login_required
@require_setup
def delivery_list(request):
    companies = DeliveryCompany.objects.all()
    return render(request, 'core/delivery_list.html', locals())


@login_required
@require_setup
def delivery_create(request):
    form = DeliveryCompanyForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'تم حفظ شركة التوصيل')
        return redirect('delivery_list')
    return render(request, 'core/form.html', {'form': form, 'title': 'شركة توصيل جديدة'})


@login_required
@require_setup
def receivables(request):
    customer_orders = [o for o in Order.objects.select_related('customer','product').filter(payment_method='unpaid') if o.remaining_amount > 0]
    delivery_orders = [o for o in Order.objects.select_related('customer','product','delivery_company').filter(payment_method='delivery') if o.remaining_amount > 0]
    return render(request, 'core/receivables.html', locals())


@login_required
@require_setup
def reports(request):
    orders_count = Order.objects.count()
    sales = sum([o.total_amount for o in Order.objects.all()], Decimal('0'))
    profit = sum([o.profit for o in Order.objects.exclude(status__in=['returned','cancelled','rejected'])], Decimal('0'))
    return render(request, 'core/reports.html', locals())


def xlsx_response(filename, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@login_required
@require_setup
def export_orders_xlsx(request):
    rows = [[o.id, o.order_date.strftime('%Y-%m-%d'), o.customer.name, o.customer.phone, o.product.name, o.quantity, o.get_status_display(), o.get_payment_method_display(), float(o.total_amount), float(o.paid_amount), float(o.remaining_amount)] for o in Order.objects.select_related('customer','product')]
    return xlsx_response('orders.xlsx', ['ID','Date','Customer','Phone','Product','Qty','Status','Payment','Total','Paid','Remaining'], rows)


@login_required
@require_setup
def export_inventory_xlsx(request):
    rows = [[p.sku, p.name, p.category, p.stock_quantity, float(p.selling_price), float(p.cost_price)] for p in Product.objects.all()]
    return xlsx_response('inventory.xlsx', ['SKU','Product','Category','Stock','Selling Price','Cost Price'], rows)


@login_required
@require_setup
def export_receivables_xlsx(request):
    rows = [[o.id, o.customer.name, o.customer.phone, o.product.name, o.get_payment_method_display(), o.delivery_company.name if o.delivery_company else '', float(o.remaining_amount)] for o in Order.objects.select_related('customer','product','delivery_company') if o.remaining_amount > 0]
    return xlsx_response('receivables.xlsx', ['Order','Customer','Phone','Product','Type','Delivery Company','Remaining'], rows)
