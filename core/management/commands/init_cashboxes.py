from django.core.management.base import BaseCommand
from core.models import CashBox, Payment

class Command(BaseCommand):
    help = 'Create empty cashboxes for each payment method without demo data.'

    def handle(self, *args, **options):
        for key, label in Payment.METHOD_CHOICES:
            obj, created = CashBox.objects.get_or_create(name=f'صندوق {label}', defaults={'currency':'JOD','opening_balance':0,'notes':'صندوق افتراضي لطريقة الدفع'})
            self.stdout.write(self.style.SUCCESS(('Created' if created else 'Exists') + f': {obj.name}'))
