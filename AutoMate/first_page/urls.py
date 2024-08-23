from django.urls import path
from . import views

app_name = 'first_page'

urlpatterns = [
    path('', views.home, name='home'),
    path('SplunkRRN', views.SplunkRRN, name='SplunkRRN'),
    path('splunk2sender/', views.splunk2sender, name='splunk2sender'),
    path('json2yaml/', views.json2yaml, name='json2yaml'), 

]
