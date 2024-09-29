from django.urls import path
from . import views

app_name = 'slot_booking'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('save-booking/', views.save_booking, name='save_booking'),  # URL for saving booking
    path('get-bookings/', views.get_bookings, name='get_bookings'),  # New URL for fetching bookings
    path('delete-booking/<int:booking_id>/', views.delete_booking, name='delete_booking'),  # New route for deleting booking
    path('add-cron-job/', views.add_cron_job, name='add_cron_job'),

]
