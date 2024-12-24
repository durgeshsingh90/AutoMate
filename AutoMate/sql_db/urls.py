from django.urls import path
from .views import list_tables, select_all_from_table, index

urlpatterns = [
    path('', index, name='index'),
    path('list_tables/', list_tables, name='list_tables'),
    path('select_all_from_table/<str:table_name>/', select_all_from_table, name='select_all_from_table'),
]
