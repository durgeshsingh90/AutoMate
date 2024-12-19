from django.urls import path
from . import views

urlpatterns = [
    path('', views.run_sql_commands, name='run_sql_commands'),
    path('update_tables/', views.update_table_names, name='update_table_names'),
    path('fetch_table_data/<str:table_name>/', views.fetch_table_data, name='fetch_table_data'),
    path('delete_table_data/<str:table_name>/', views.delete_table_data, name='delete_table_data'),
]
