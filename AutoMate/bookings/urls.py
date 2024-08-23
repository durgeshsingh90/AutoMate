# bookings/urls.py
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.calendar_view, name='booking'),
    path('delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('check-availability/', views.check_availability, name='check_availability'),
    path('book/', views.book_booking, name='book_booking'),
    path('ajax/load-scheme-types/', views.load_scheme_types, name='ajax_load_scheme_types'),  # Add this line

]
