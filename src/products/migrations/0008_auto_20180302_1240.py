# Generated by Django 2.0 on 2018-03-02 12:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_auto_20180302_1233'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loginresult',
            name='user',
        ),
        migrations.DeleteModel(
            name='LoginResult',
        ),
    ]
