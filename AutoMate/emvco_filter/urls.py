from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('format-xml/', views.format_xml_view, name='format_xml'),
  path('settings/', views.settings_editor, name='settings_page'),
    path('settings-json/', views.get_settings_json, name='get_settings_json'),
    path('save-settings/', views.save_settings_json, name='save_settings_json'),
    path('get-config-list/', views.get_settings_list, name='get_settings_list'),

]
