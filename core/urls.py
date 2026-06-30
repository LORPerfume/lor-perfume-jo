from django.urls import path
from . import views
urlpatterns=[
    path('', views.dashboard, name='dashboard'),
    path('customers/', views.customer_list, name='customer_list'), path('customers/new/', views.customer_create, name='customer_create'), path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('products/', views.product_list, name='product_list'), path('products/new/', views.product_create, name='product_create'),
    path('delivery/', views.delivery_list, name='delivery_list'), path('delivery/new/', views.delivery_create, name='delivery_create'),
    path('orders/', views.order_list, name='order_list'), path('orders/new/', views.order_create, name='order_create'), path('orders/<int:pk>/', views.order_detail, name='order_detail'), path('orders/<int:pk>/edit/', views.order_edit, name='order_edit'), path('orders/<int:pk>/invoice/', views.invoice, name='invoice'),
    path('payments/new/', views.payment_create, name='payment_create'), path('followups/', views.followup_list, name='followup_list'), path('followups/new/', views.followup_create, name='followup_create'),
    path('cashboxes/', views.cashbox_list, name='cashbox_list'), path('cashboxes/transaction/new/', views.cash_transaction_create, name='cash_transaction_create'), path('expenses/new/', views.expense_create, name='expense_create'), path('reports/', views.reports, name='reports'),
]
