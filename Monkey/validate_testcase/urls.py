from django.urls import path
from .views import upload_logs

urlpatterns = [
    path('', upload_logs, name='index'),
]
