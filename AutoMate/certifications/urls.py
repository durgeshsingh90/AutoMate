from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('testbook/', views.testbook, name='testbook'),
    path('update_test_cases/', views.update_test_cases, name='update_test_cases'),
    path('build/', views.build, name='build'),
]
