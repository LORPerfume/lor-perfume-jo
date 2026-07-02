from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.order_create, name='order_create'),
    path('orders/<int:pk>/quick-update/', views.order_quick_update, name='order_quick_update'),
    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.product_create, name='product_create'),
    path('delivery/', views.delivery_list, name='delivery_list'),
    path('delivery/new/', views.delivery_create, name='delivery_create'),
    path('inventory/', views.inventory, name='inventory'),
    path('inventory/in/', views.inventory_in, name='inventory_in'),
    path('cashboxes/', views.cashboxes, name='cashboxes'),
    path('cashboxes/new/', views.cashbox_create, name='cashbox_create'),
    path('receivables/', views.receivables, name='receivables'),
    path('reports/', views.reports, name='reports'),
    path('export/orders.xlsx', views.export_orders_xlsx, name='export_orders_xlsx'),
    path('export/inventory.xlsx', views.export_inventory_xlsx, name='export_inventory_xlsx'),
    path('export/receivables.xlsx', views.export_receivables_xlsx, name='export_receivables_xlsx'),
]
