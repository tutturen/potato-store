# Generated by Django 2.0 on 2018-03-23 13:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_auto_20180304_1339'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stockValue',
            field=models.FloatField(default=1, verbose_name='Stock value'),
            preserve_default=False,
        ),
    ]