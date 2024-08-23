#AutoMate\binblocking\admin.py
from django import forms
from django.contrib import admin
from .models import DatabaseConnection

class DatabaseConnectionForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = DatabaseConnection
        fields = '__all__'

@admin.register(DatabaseConnection)
class DatabaseConnectionAdmin(admin.ModelAdmin):
    form = DatabaseConnectionForm
    list_display = ('environment', 'name', 'username', 'table_name')
    list_filter = ('environment',)
    search_fields = ('username', 'table_name', 'name')
