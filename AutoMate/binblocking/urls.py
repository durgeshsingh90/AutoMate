from django.urls import path
from .views import process_bins, display_processed_bins

app_name = 'binblocking'
urlpatterns = [
    path('', process_bins, name='process_bins'),
    path('display-processed-bins/', display_processed_bins, name='display_processed_bins')

]
