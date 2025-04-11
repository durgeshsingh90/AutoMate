from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('execute_queries/', views.execute_queries_view, name='execute_queries'),
    path('save_script/', views.save_script_view, name='save_script'),
    path('load_scripts/', views.load_scripts_view, name='load_scripts'),
]
