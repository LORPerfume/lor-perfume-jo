from django.core.management.base import BaseCommand, CommandError
from core.models import Customer, Product, Order, Payment, CashBox, CashTransaction, InventoryMovement, ReturnRecord, Expense, DeliveryCompany

class Command(BaseCommand):
    help = 'Verify that the business database is empty: no demo data and no business records.'

    def handle(self, *args, **options):
        checks = {
            'customers': Customer.objects.count(),
            'products': Product.objects.count(),
            'orders': Order.objects.count(),
            'payments': Payment.objects.count(),
            'cashboxes': CashBox.objects.count(),
            'cash_transactions': CashTransaction.objects.count(),
            'inventory_movements': InventoryMovement.objects.count(),
            'returns': ReturnRecord.objects.count(),
            'expenses': Expense.objects.count(),
            'delivery_companies': DeliveryCompany.objects.count(),
        }
        bad = {k: v for k, v in checks.items() if v}
        if bad:
            raise CommandError(f'Not empty: {bad}')
        self.stdout.write(self.style.SUCCESS('OK: business database is empty.'))
