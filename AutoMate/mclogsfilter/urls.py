from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_log_file, name='upload_log_file'),
]
