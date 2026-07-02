from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('core', '0004_alter_payment_method')]
    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('cash','نقدي'),('cliq','كليك'),('bank','تحويل بنكي'),('card','بطاقة/فيزا'),('delivery','ذمم شركة التوصيل'),('wallet','محفظة إلكترونية'),('other','أخرى')], db_index=True, default='delivery', max_length=30, verbose_name='طريقة الدفع المتفق عليها'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='method',
            field=models.CharField(choices=[('cash','نقدي'),('cliq','كليك'),('bank','تحويل بنكي'),('card','بطاقة/فيزا'),('delivery','ذمم شركة التوصيل'),('wallet','محفظة إلكترونية'),('other','أخرى')], default='cash', max_length=30, verbose_name='طريقة الدفع'),
        ),
    ]
