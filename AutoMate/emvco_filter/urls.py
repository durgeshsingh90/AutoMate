from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('format-xml/', views.format_xml_view, name='format_xml'),
]
