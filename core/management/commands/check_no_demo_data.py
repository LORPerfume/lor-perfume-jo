from django.core.management.base import BaseCommand, CommandError
from core.models import Product, Order, InventoryMovement, ReturnRecord, Customer

class Command(BaseCommand):
    help = 'Verify that the system has no known demo/sample records.'

    def handle(self, *args, **options):
        product_hits = Product.objects.filter(name__in=['lor perfume', 'باقة متابعة VIP', 'متابعة طلب خاص']) | Product.objects.filter(sku__in=['001', 'PKG-002', 'SRV-001'])
        customer_hits = Customer.objects.filter(name__in=['عميل تجريبي', 'Demo Customer', 'زبون تجريبي'])
        if product_hits.exists() or customer_hits.exists():
            raise CommandError('Demo data still exists. Run migrations or remove old database records.')
        self.stdout.write(self.style.SUCCESS('OK: no known demo data found.'))
