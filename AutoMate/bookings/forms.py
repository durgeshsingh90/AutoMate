from django import forms
from .models import Booking, Scheme, SchemeType
from sender.models import ServerConfig
from datetime import datetime, timedelta
import re
import paramiko
from django.db import transaction
import logging

# Set up logging
logger = logging.getLogger(__name__)

class BookingForm(forms.ModelForm):
    TIME_SLOT_CHOICES = [
        ('AM', 'AM (8AM - 1PM)'),
        ('PM', 'PM (1PM - 6PM)'),
        ('Overnight', 'Overnight (6PM - 8AM)'),
    ]
    WEEKDAYS_CHOICES = [
        ('MO', 'Monday'),
        ('TU', 'Tuesday'),
        ('WE', 'Wednesday'),
        ('TH', 'Thursday'),
        ('FR', 'Friday'),
        ('SA', 'Saturday'),
        ('SU', 'Sunday'),
    ]

    date_range = forms.CharField(
        label='Date Range',
        widget=forms.TextInput(attrs={'autocomplete': 'off', 'required': 'required'})
    )
    time_slot = forms.MultipleChoiceField(
        choices=TIME_SLOT_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'required': 'required'}),
        label='Time Slot'
    )
    server = forms.ModelChoiceField(
        queryset=ServerConfig.objects.all(),
        label='Server',
        required=True
    )
    scheme = forms.ModelMultipleChoiceField(
        queryset=Scheme.objects.all(),
        label='Scheme Name',
        required=True,
        widget=forms.CheckboxSelectMultiple
    )
    scheme_type = forms.ModelMultipleChoiceField(
        queryset=SchemeType.objects.none(),
        label='Scheme Type',
        required=True,
        widget=forms.CheckboxSelectMultiple
    )
    recurrence_days = forms.MultipleChoiceField(
        choices=WEEKDAYS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='Repeat on Days',
        required=False
    )

    class Meta:
        model = Booking
        fields = [
            'project_name', 'psp_name', 'owner',
            'date_range', 'time_slot', 'server', 'scheme', 'scheme_type', 'recurrence_days'
        ]
        widgets = {
            'project_name': forms.TextInput(attrs={'required': 'required'}),
            'psp_name': forms.TextInput(attrs={'required': 'required'}),
            'owner': forms.TextInput(attrs={'required': 'required'}),
        }

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        if 'scheme' in self.data:
            try:
                scheme_ids = self.data.getlist('scheme')
                self.fields['scheme_type'].queryset = SchemeType.objects.filter(scheme_id__in=scheme_ids).order_by('type_name')
                logger.info("Scheme types have been updated based on the scheme selection.")
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to filter scheme types: {e}")
                self.fields['scheme_type'].queryset = SchemeType.objects.none()

    def clean_date_range(self):
        date_range = self.cleaned_data.get('date_range')
        try:
            start_date_str, end_date_str = date_range.split(' - ')
            start_date = datetime.strptime(start_date_str, '%m/%d/%Y').date()
            end_date = datetime.strptime(end_date_str, '%m/%d/%Y').date()
            self.cleaned_data['start_date'] = start_date
            self.cleaned_data['end_date'] = end_date
            logger.info("Date range parsed and validated.")
        except ValueError as e:
            logger.error("Invalid date format: {e}")
            raise forms.ValidationError("Invalid date format. Use MM/DD/YYYY - MM/DD/YYYY.")
        return date_range

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        server = cleaned_data.get('server')
        time_slot = ','.join(cleaned_data.get('time_slot'))
        schemes = cleaned_data.get('scheme')
        recurrence_days = cleaned_data.get('recurrence_days')

        if start_date and end_date and server and schemes:
            current_date = start_date
            while current_date <= end_date:
                if not recurrence_days or current_date.strftime('%a').upper()[:2] in recurrence_days:
                    existing_bookings = Booking.objects.filter(
                        start_date__lte=current_date,
                        end_date__gte=current_date,
                        server=server,
                        time_slot=time_slot,
                        scheme__in=schemes
                    ).distinct()
                    if existing_bookings.exists():
                        logger.warning(f"Overlapping booking exists for {current_date}.")
                        raise forms.ValidationError(f"Overlapping booking exists for {current_date}. Please adjust your booking.")
                current_date += timedelta(days=1)
        logger.info("Form validation completed successfully.")
        return cleaned_data

    def save(self, commit=True):
        with transaction.atomic():
            instance = super().save(commit=False)
            instance.start_date = self.cleaned_data['start_date']
            instance.end_date = self.cleaned_data['end_date']
            instance.time_slot = ','.join(self.cleaned_data['time_slot'])
            instance.save()  # Saving the instance before accessing many-to-many fields
            self.save_m2m()

            ssh_client = self._generate_ssh_command(instance)
            if ssh_client:
                try:
                    self._generate_booking_script(ssh_client, instance)
                    self._generate_cron_schedule(ssh_client, instance)
                    logger.info("Booking and cron schedule have been successfully set up.")
                finally:
                    ssh_client.close()
            else:
                logger.error("Failed to establish an SSH connection.")
                raise forms.ValidationError("Failed to connect to the server.")

            logger.info(f"Booking ID {instance.booking_id} created and saved.")
            return instance
