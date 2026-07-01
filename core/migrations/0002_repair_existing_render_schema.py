# Repair migration for Render databases that already had core.0001 applied from the older project.
# The first public v2 zip shipped a new 0001_initial.py, but existing Render DBs do not rerun
# migrations that are already marked as applied. This migration safely adds the physical
# columns/tables that v2 needs if they are missing. It is no-op on fresh databases.

from django.db import migrations


def _columns(connection, table_name):
    with connection.cursor() as cursor:
        return {col.name for col in connection.introspection.get_table_description(cursor, table_name)}


def repair_schema(apps, schema_editor):
    connection = schema_editor.connection
    existing_tables = set(connection.introspection.table_names())

    Customer = apps.get_model('core', 'Customer')
    Order = apps.get_model('core', 'Order')
    Task = apps.get_model('core', 'Task')
    Note = apps.get_model('core', 'Note')
    Attachment = apps.get_model('core', 'Attachment')

    # Older production databases had core_customer without these v2 fields.
    if Customer._meta.db_table in existing_tables:
        customer_cols = _columns(connection, Customer._meta.db_table)
        for field_name in ['email', 'grade', 'last_contact_at', 'next_action_date']:
            if field_name not in customer_cols:
                schema_editor.add_field(Customer, Customer._meta.get_field(field_name))

    # Older production databases had core_order without due_date.
    if Order._meta.db_table in existing_tables:
        order_cols = _columns(connection, Order._meta.db_table)
        if 'due_date' not in order_cols:
            schema_editor.add_field(Order, Order._meta.get_field('due_date'))

    # These models are new in v2. Create their tables if the DB came from v1.
    existing_tables = set(connection.introspection.table_names())
    for model in [Task, Note, Attachment]:
        if model._meta.db_table not in existing_tables:
            schema_editor.create_model(model)
            existing_tables.add(model._meta.db_table)


def noop_reverse(apps, schema_editor):
    # Intentionally irreversible: this migration only repairs missing production schema.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(repair_schema, noop_reverse),
    ]
