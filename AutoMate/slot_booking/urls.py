from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', views.admin, name='admin'),
    path('config.json', views.config, name='config'),
    path('submit/', views.save_submission, name='submit')
]
