# Generated by Django 5.0.6 on 2024-08-11 15:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_remove_booking_schemes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='every',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='frequency',
        ),
        migrations.RemoveField(
            model_name='booking',
            name='repeat',
        ),
    ]
