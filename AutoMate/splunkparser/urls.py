# splunkparser/urls.py

from django.urls import path
from .views import parse_logs
from django.shortcuts import render

def index(request):
    return render(request, 'splunkparser/parser.html')

urlpatterns = [
    path('', index, name='index'),
    path('parse_logs/', parse_logs, name='parse_logs'),  # Update the URL pattern to point to the new view
]
