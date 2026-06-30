from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission
from core.models import Product, Customer, DeliveryCompany, CashBox, Order, Payment, FollowUp, Expense
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help='Create demo data for Sarh Pro OMS'
    def handle(self,*args,**kwargs):
        user,_=User.objects.get_or_create(username='admin', defaults={'is_staff':True,'is_superuser':True})
        user.set_password('admin12345'); user.is_staff=True; user.is_superuser=True; user.save()
        box,_=CashBox.objects.get_or_create(name='الصندوق الرئيسي', defaults={'opening_balance':500})
        d,_=DeliveryCompany.objects.get_or_create(name='شركة التوصيل السريع', defaults={'default_fee':3})
        p1,_=Product.objects.get_or_create(sku='SKU-001', defaults={'name':'المنتج الرئيسي','category':'منتجات رئيسية','selling_price':25,'cost_price':11,'stock_quantity':40})
        p2,_=Product.objects.get_or_create(sku='SKU-002', defaults={'name':'باقة مميزة','category':'عروض','selling_price':45,'cost_price':20,'stock_quantity':4})
        c1,_=Customer.objects.get_or_create(phone='0790000001', defaults={'name':'أحمد محمد','city':'عمّان','area':'خلدا','source':'Instagram'})
        c2,_=Customer.objects.get_or_create(phone='0780000002', defaults={'name':'سارة علي','city':'إربد','area':'الحي الشرقي','source':'Facebook'})
        o1,_=Order.objects.get_or_create(customer=c1, product=p1, defaults={'quantity':2,'unit_price':25,'delivery_company':d,'delivery_fee':3,'status':'confirmed','priority':'high','assigned_to':user})
        o2,_=Order.objects.get_or_create(customer=c2, product=p2, defaults={'quantity':1,'unit_price':45,'delivery_company':d,'delivery_fee':3,'status':'with_delivery','assigned_to':user})
        Payment.objects.get_or_create(order=o1, amount=Decimal('30'), method='cash', cashbox=box)
        FollowUp.objects.get_or_create(customer=c2, order=o2, result='call_later', defaults={'note':'التواصل غداً لتأكيد الاستلام','next_followup_date':timezone.localdate(),'assigned_to':user})
        Expense.objects.get_or_create(category='ads', amount=Decimal('15'), description='إعلان ممول', cashbox=box)
        self.stdout.write(self.style.SUCCESS('Demo ready. Login: admin / admin12345'))
