# Generated to remove the demo/seed records that appeared in the previous package.
from django.db import migrations

DEMO_PRODUCT_NAMES = ['lor perfume', 'باقة متابعة VIP', 'متابعة طلب خاص']
DEMO_SKUS = ['001', 'PKG-002', 'SRV-001']

def remove_demo_records(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    InventoryMovement = apps.get_model('core', 'InventoryMovement')
    ReturnRecord = apps.get_model('core', 'ReturnRecord')
    Order = apps.get_model('core', 'Order')
    Payment = apps.get_model('core', 'Payment')
    CashTransaction = apps.get_model('core', 'CashTransaction')
    Customer = apps.get_model('core', 'Customer')
    FollowUp = apps.get_model('core', 'FollowUp')
    Task = apps.get_model('core', 'Task')
    Note = apps.get_model('core', 'Note')
    Expense = apps.get_model('core', 'Expense')
    ActivityLog = apps.get_model('core', 'ActivityLog')

    demo_products = Product.objects.filter(name__in=DEMO_PRODUCT_NAMES) | Product.objects.filter(sku__in=DEMO_SKUS)
    demo_product_ids = list(demo_products.values_list('id', flat=True))

    if demo_product_ids:
        CashTransaction.objects.filter(source_payment__order__product_id__in=demo_product_ids).delete()
        Payment.objects.filter(order__product_id__in=demo_product_ids).delete()
        ReturnRecord.objects.filter(product_id__in=demo_product_ids).delete()
        InventoryMovement.objects.filter(product_id__in=demo_product_ids).delete()
        FollowUp.objects.filter(order__product_id__in=demo_product_ids).delete()
        Task.objects.filter(order__product_id__in=demo_product_ids).delete()
        Note.objects.filter(order__product_id__in=demo_product_ids).delete()
        Order.objects.filter(product_id__in=demo_product_ids).delete()
        Product.objects.filter(id__in=demo_product_ids).delete()

    Customer.objects.filter(name__in=['عميل تجريبي', 'Demo Customer', 'زبون تجريبي']).delete()
    Expense.objects.filter(description__icontains='تجريبي').delete()
    ActivityLog.objects.filter(description__icontains='تجريبي').delete()


def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [('core', '0005_order_payment_method')]
    operations = [migrations.RunPython(remove_demo_records, noop)]
