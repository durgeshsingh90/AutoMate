from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('upload_log/', views.upload_log),
    path('zip_filtered_files/', views.zip_filtered_files),
    path('download_filtered/', views.download_filtered_by_de032),

]
