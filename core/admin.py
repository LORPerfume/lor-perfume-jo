from django.contrib import admin
from .models import Product, Customer, DeliveryCompany, Order, Payment, CashBox, CashTransaction, FollowUp, Expense, ActivityLog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=('sku','name','category','selling_price','cost_price','stock_quantity','stock_status','is_active')
    search_fields=('sku','name','category'); list_filter=('category','is_active')
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display=('name','phone','city','area','source','created_at')
    search_fields=('name','phone','city','area','tags'); list_filter=('city','source')
@admin.register(DeliveryCompany)
class DeliveryCompanyAdmin(admin.ModelAdmin):
    list_display=('name','phone','default_fee','is_active'); search_fields=('name','phone')
class PaymentInline(admin.TabularInline): model=Payment; extra=0
class FollowUpInline(admin.TabularInline): model=FollowUp; extra=0
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=('id','customer','product','status','payment_status','priority','total_amount','paid_amount','remaining_amount','profit','order_date')
    list_filter=('status','payment_status','priority','delivery_company','order_date')
    search_fields=('customer__name','customer__phone','delivery_tracking_number','product__name')
    date_hierarchy='order_date'; inlines=[PaymentInline,FollowUpInline]
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display=('order','amount','method','cashbox','payment_date','reference'); list_filter=('method','cashbox','payment_date')
@admin.register(CashBox)
class CashBoxAdmin(admin.ModelAdmin): list_display=('name','opening_balance','currency','balance')
@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin): list_display=('cashbox','transaction_type','amount','description','date'); list_filter=('transaction_type','cashbox','date')
@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin): list_display=('customer','order','result','next_followup_date','assigned_to','created_at'); list_filter=('result','next_followup_date','assigned_to')
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin): list_display=('category','amount','cashbox','description','date'); list_filter=('category','cashbox','date')
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin): list_display=('user','action','model_name','object_id','created_at'); list_filter=('action','model_name','created_at')
