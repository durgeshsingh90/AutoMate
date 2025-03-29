from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('upload_log/', views.upload_log),
    path('check_progress/', views.check_filter_progress),
    path('zip_filtered_files/', views.zip_filtered_files),
    path('convert_to_emvco/', views.convert_to_emvco),

]
