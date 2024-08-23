# bookings/models.py
from django.db import models

from django.db import models
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
class Booking(models.Model):
    booking_id = models.PositiveIntegerField()
    project_name = models.CharField(max_length=255)
    psp_name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255, verbose_name="Owner")
    start_date = models.DateField()
    end_date = models.DateField()
    time_slot = models.CharField(max_length=50)
    server = models.ForeignKey('sender.ServerConfig', on_delete=models.CASCADE)
    scheme = models.ManyToManyField('Scheme')
    scheme_type = models.ManyToManyField('SchemeType')

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        # Generate the booking_id if it doesn't exist
        if not self.booking_id:
            current_year = datetime.now().year
            # Find the highest booking_id for the current year
            last_booking = Booking.objects.filter(start_date__year=current_year).order_by('booking_id').last()
            if last_booking:
                self.booking_id = last_booking.booking_id + 1
            else:
                self.booking_id = 1  # Start from 1 if no bookings exist for the year

        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"Created new Booking with ID: {self.booking_id}")
        else:
            logger.info(f"Updated Booking with ID: {self.booking_id}")



    def __str__(self):
        return f"{self.project_name} - {self.psp_name}"

class Scheme(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class SchemeType(models.Model):
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='types')
    type_name = models.CharField(max_length=300)

    def __str__(self):
        return f"{self.type_name} ({self.scheme.name})"
