from django.contrib import admin
from .models import Product, Customer, DeliveryCompany, Order, Payment, CashBox, CashTransaction, FollowUp, Expense

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'selling_price', 'cost_price', 'stock_quantity', 'is_active')
    search_fields = ('name',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'city', 'area', 'created_at')
    search_fields = ('name', 'phone', 'city', 'area')
    list_filter = ('city',)

@admin.register(DeliveryCompany)
class DeliveryCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'default_fee')

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0

class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'payment_status', 'total_amount', 'paid_amount', 'remaining_amount', 'order_date')
    list_filter = ('status', 'payment_status', 'delivery_company')
    search_fields = ('customer__name', 'customer__phone', 'delivery_tracking_number')
    inlines = [PaymentInline, FollowUpInline]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'method', 'cashbox', 'payment_date')
    list_filter = ('method', 'cashbox')

@admin.register(CashBox)
class CashBoxAdmin(admin.ModelAdmin):
    list_display = ('name', 'opening_balance', 'balance')

@admin.register(CashTransaction)
class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ('cashbox', 'transaction_type', 'amount', 'description', 'date')
    list_filter = ('transaction_type', 'cashbox')

@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('customer', 'order', 'result', 'next_followup_date', 'created_at')
    list_filter = ('result', 'next_followup_date')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'cashbox', 'description', 'date')
    list_filter = ('category', 'cashbox')
