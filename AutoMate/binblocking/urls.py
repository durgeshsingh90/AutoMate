from django.urls import path
from .views import process_bins

app_name = 'binblocking'
urlpatterns = [
    path('', process_bins, name='process_bins'),
]
