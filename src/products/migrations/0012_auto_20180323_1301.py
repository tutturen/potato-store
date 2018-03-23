# Generated by Django 2.0 on 2018-03-23 13:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_auto_20180304_1339'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductPurchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('unitPrice', models.FloatField()),
            ],
        ),
        migrations.RemoveField(
            model_name='product',
            name='packageDeal',
        ),
        migrations.RemoveField(
            model_name='product',
            name='percentSale',
        ),
        migrations.AlterField(
            model_name='order',
            name='products',
            field=models.ManyToManyField(to='products.ProductPurchase'),
        ),
        migrations.AlterField(
            model_name='packagedeal',
            name='minimumQuantity',
            field=models.IntegerField(verbose_name='You buy'),
        ),
        migrations.AlterField(
            model_name='packagedeal',
            name='paidQuantity',
            field=models.IntegerField(verbose_name='You pay for'),
        ),
        migrations.AlterField(
            model_name='packagedeal',
            name='product',
            field=models.ManyToManyField(related_name='package_deal', to='products.Product'),
        ),
        migrations.AlterField(
            model_name='percentsale',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='percent_sale', to='products.Product'),
        ),
        migrations.AddField(
            model_name='productpurchase',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Product'),
        ),
    ]
