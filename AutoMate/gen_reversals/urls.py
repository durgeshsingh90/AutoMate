from django.urls import path
from . import views

urlpatterns = [
    path('', views.reversal_generator, name='reversal_generator'),
]
