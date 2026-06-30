from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import *
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help='Create rich demo data for LOR FollowUp Pro'
    def handle(self,*args,**kwargs):
        user,_=User.objects.get_or_create(username='admin', defaults={'is_staff':True,'is_superuser':True})
        user.set_password('admin12345'); user.is_staff=True; user.is_superuser=True; user.save()
        box,_=CashBox.objects.get_or_create(name='الصندوق الرئيسي', defaults={'opening_balance':500})
        d,_=DeliveryCompany.objects.get_or_create(name='شركة التوصيل السريع', defaults={'default_fee':3})
        p1,_=Product.objects.get_or_create(sku='SRV-001', defaults={'name':'متابعة طلب خاص','category':'خدمات','selling_price':25,'cost_price':8,'stock_quantity':40})
        p2,_=Product.objects.get_or_create(sku='PKG-002', defaults={'name':'باقة متابعة VIP','category':'باقات','selling_price':75,'cost_price':22,'stock_quantity':4})
        c1,_=Customer.objects.get_or_create(phone='0790000001', defaults={'name':'أحمد محمد','city':'عمّان','area':'خلدا','source':'Instagram','grade':'A','tags':'VIP, مهتم'})
        c2,_=Customer.objects.get_or_create(phone='0780000002', defaults={'name':'سارة علي','city':'إربد','area':'الحي الشرقي','source':'Referral','grade':'B'})
        o1,_=Order.objects.get_or_create(customer=c1, product=p1, defaults={'quantity':2,'unit_price':25,'delivery_company':d,'delivery_fee':3,'status':'confirmed','priority':'high','assigned_to':user,'due_date':timezone.localdate()})
        o2,_=Order.objects.get_or_create(customer=c2, product=p2, defaults={'quantity':1,'unit_price':75,'delivery_company':d,'delivery_fee':3,'status':'waiting','assigned_to':user,'due_date':timezone.localdate()})
        Payment.objects.get_or_create(order=o1, amount=Decimal('30'), method='cash', cashbox=box)
        FollowUp.objects.get_or_create(customer=c2, order=o2, result='call_later', defaults={'note':'التواصل غداً لتأكيد التفاصيل','next_followup_date':timezone.localdate(),'assigned_to':user})
        Task.objects.get_or_create(title='مراجعة العملاء المتأخرين', defaults={'description':'فتح قائمة المتابعات ومعالجة المتأخر','due_date':timezone.localdate(),'priority':'urgent','assigned_to':user})
        Note.objects.get_or_create(customer=c1, title='ملاحظة مهمة', defaults={'body':'العميل يفضل التواصل واتساب بعد العصر','created_by':user})
        Expense.objects.get_or_create(category='ads', amount=Decimal('15'), description='إعلان ممول', cashbox=box)
        ActivityLog.objects.get_or_create(user=user,action='تهيئة بيانات تجريبية',model_name='System',description='تم إنشاء بيانات أولية للنظام')
        self.stdout.write(self.style.SUCCESS('Demo ready. Login: admin / admin12345'))
