# Generated by Django 5.0.6 on 2024-08-11 15:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='schemes',
        ),
    ]
