from django.urls import path
from . import views
urlpatterns=[
path('',views.dashboard,name='dashboard'), path('search/',views.global_search,name='global_search'),
path('customers/',views.customer_list,name='customer_list'), path('customers/new/',views.customer_create,name='customer_create'), path('customers/<int:pk>/',views.customer_detail,name='customer_detail'), path('customers/<int:pk>/edit/',views.customer_edit,name='customer_edit'),
path('orders/',views.order_list,name='order_list'), path('orders/new/',views.order_create,name='order_create'), path('orders/<int:pk>/',views.order_detail,name='order_detail'), path('orders/<int:pk>/edit/',views.order_edit,name='order_edit'),
path('products/',views.product_list,name='product_list'), path('products/new/',views.product_create,name='product_create'), path('products/<int:pk>/edit/',views.product_edit,name='product_edit'),
path('inventory/',views.inventory_list,name='inventory_list'), path('inventory/movement/new/',views.inventory_movement_create,name='inventory_movement_create'), path('returns/new/',views.return_create,name='return_create'),
path('followups/',views.followup_list,name='followup_list'), path('followups/new/',views.followup_create,name='followup_create'),
path('tasks/',views.task_list,name='task_list'), path('tasks/new/',views.task_create,name='task_create'), path('tasks/<int:pk>/done/',views.task_done,name='task_done'),
path('cashboxes/',views.cashbox_list,name='cashbox_list'), path('cashboxes/transaction/new/',views.cash_transaction_create,name='cash_transaction_create'), path('payments/new/',views.payment_create,name='payment_create'), path('expenses/new/',views.expense_create,name='expense_create'),
path('delivery/',views.delivery_list,name='delivery_list'), path('delivery/new/',views.delivery_create,name='delivery_create'), path('delivery/statement/',views.delivery_statement,name='delivery_statement'),
path('notes/new/',views.note_create,name='note_create'), path('attachments/new/',views.attachment_create,name='attachment_create'),
path('calendar/',views.calendar_view,name='calendar'), path('reports/',views.reports,name='reports'), path('export/orders.csv',views.export_orders_csv,name='export_orders_csv'), path('export/inventory.csv',views.export_inventory_csv,name='export_inventory_csv'), path('export/orders.xlsx',views.export_orders_xlsx,name='export_orders_xlsx'), path('export/inventory.xlsx',views.export_inventory_xlsx,name='export_inventory_xlsx'), path('export/receivables.xlsx',views.export_receivables_xlsx,name='export_receivables_xlsx'),
]
