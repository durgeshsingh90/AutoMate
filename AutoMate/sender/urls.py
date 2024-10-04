from django.urls import path
from . import views

app_name = 'sender'

urlpatterns = [
    path('', views.home, name='home'),  # Home page to display Monaco editor
    path('save_test_case/', views.save_test_case, name='save_test_case'),  # URL for saving test case
    # path('edit_test_case/<str:test_case_name>/', views.edit_test_case, name='edit_test_case'),  # Edit test case
]
