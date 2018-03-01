# Generated by Django 2.0 on 2018-02-27 13:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('totalBeforeDiscount', models.FloatField()),
                ('totalDiscount', models.FloatField()),
                ('total', models.FloatField()),
                ('products', models.ManyToManyField(to='products.Product')),
            ],
        ),
        migrations.CreateModel(
            name='LoginResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('success', models.BooleanField()),
                ('token', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Receipt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('success', models.BooleanField()),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Cart')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('firstName', models.CharField(max_length=100)),
                ('lastName', models.CharField(max_length=100)),
                ('username', models.CharField(max_length=50)),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.Cart')),
            ],
        ),
        migrations.AddField(
            model_name='loginresult',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.User'),
        ),
    ]