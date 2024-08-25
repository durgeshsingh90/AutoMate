from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'first_page'

urlpatterns = [
    path('', views.home, name='home'),
]
