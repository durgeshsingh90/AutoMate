from django.urls import path
from . import views

app_name = 'sender'

urlpatterns = [
    path('', views.home, name='home'),
    path('server-config/', views.server_config, name='server_config'),
    path('send-transaction/<int:server_id>/', views.send_transaction, name='send_transaction'),
    path('yaml-schema-config/', views.yaml_schema_config, name='yaml_schema_config'),
    path('get-field-definitions/', views.get_field_definitions, name='get_field_definitions'),

]
