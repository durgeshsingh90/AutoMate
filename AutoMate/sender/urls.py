from django.urls import path
from . import views

app_name = 'sender'  # Optional, if you want to namespace your app

urlpatterns = [
    path('', views.home, name='home'),  # Home page to display Monaco editor
    path('save-json/<str:filename>', views.save_json, name='save_json'),  # Save JSON file
    path('get-json-files/', views.get_json_files, name='get_json_files'),  # Fetch JSON files
    path('create-folder/', views.create_folder, name='create_folder'),
    path('move-file/', views.move_file, name='move_file'),

]
