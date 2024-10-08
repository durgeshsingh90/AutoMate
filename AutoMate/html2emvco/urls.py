from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_log, name='home'),  # Default route redirects to upload page

    path('upload/', views.upload_log, name='upload_log'),  # Route for file upload
    path('result/', views.result_log, name='result_log'),  # Route for result display
]
