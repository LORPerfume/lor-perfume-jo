# This migration intentionally empties all business data from the OrderFlow system.
# It is included because previous packages/deployments contained sample/demo records.
# It preserves Django users/admin accounts, but removes orders, products, customers,
# inventory movements, cashboxes, payments, delivery companies, reports source data, etc.

from django.db import migrations, connection


def wipe_business_data(apps, schema_editor):
    model_names = [
        'ActivityLog',
        'Attachment',
        'Note',
        'Task',
        'FollowUp',
        'ReturnRecord',
        'InventoryMovement',
        'Expense',
        'CashTransaction',
        'Payment',
        'Order',
        'Product',
        'Customer',
        'DeliveryCompany',
        'CashBox',
    ]

    # Delete through historical models so it works safely during migration.
    for model_name in model_names:
        try:
            Model = apps.get_model('core', model_name)
            Model.objects.all().delete()
        except LookupError:
            pass

    # Reset auto-increment sequences where the database supports Django sequence reset SQL.
    try:
        models = []
        for model_name in model_names:
            try:
                models.append(apps.get_model('core', model_name))
            except LookupError:
                pass
        sql_list = connection.ops.sequence_reset_sql(no_style(), models)
        with connection.cursor() as cursor:
            for sql in sql_list:
                cursor.execute(sql)
    except Exception:
        # Sequence reset is optional; data deletion above is the important part.
        pass


def noop(apps, schema_editor):
    pass


def no_style():
    from django.core.management.color import no_style as _no_style
    return _no_style()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_remove_demo_seed_records'),
    ]

    operations = [
        migrations.RunPython(wipe_business_data, noop),
    ]
