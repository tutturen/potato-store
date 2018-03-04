# Generated by Django 2.0 on 2018-03-02 12:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_auto_20180302_1228'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='orders',
        ),
        migrations.AddField(
            model_name='order',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products.User'),
            preserve_default=False,
        ),
    ]
