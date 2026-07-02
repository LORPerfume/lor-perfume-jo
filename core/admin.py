from django.contrib import admin
from .models import *
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(DeliveryCompany)
admin.site.register(CashBox)
admin.site.register(Order)
admin.site.register(InventoryMovement)
admin.site.register(Payment)
admin.site.register(CashTransaction)
