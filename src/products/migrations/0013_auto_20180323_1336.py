# Generated by Django 2.0 on 2018-03-23 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_auto_20180323_1301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(related_name='purchases', to='products.ProductPurchase'),
        ),
    ]
