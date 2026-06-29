from django.contrib import admin
from django.urls import path, include
from core import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', views.dashboard, name='dashboard'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/new/', views.customer_create, name='customer_create'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('payments/new/', views.payment_create, name='payment_create'),
    path('followups/new/', views.followup_create, name='followup_create'),
    path('cashboxes/', views.cashbox_list, name='cashbox_list'),
    path('cashboxes/transaction/new/', views.cash_transaction_create, name='cash_transaction_create'),
    path('expenses/new/', views.expense_create, name='expense_create'),
]
