from django.urls import path
from .views import list_tables, select_all_from_table, index, refresh_list_tables, refresh_select_all_from_table

urlpatterns = [
    path('', index, name='index'),
    path('list_tables/', list_tables, name='list_tables'),
    path('select_all_from_table/<str:table_name>/', select_all_from_table, name='select_all_from_table'),
    path('refresh_list_tables/', refresh_list_tables, name='refresh_list_tables'),  # Add this line
    path('refresh_select_all_from_table/<str:table_name>/', refresh_select_all_from_table, name='refresh_select_all_from_table'),

]

