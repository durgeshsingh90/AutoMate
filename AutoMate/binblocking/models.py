# AutoMate\binblocking\models.py
from django.db import models

class DatabaseConnection(models.Model):
    ENV_CHOICES = [
        ('PROD', 'Production'),
        ('UAT', 'UAT'),
    ]
    
    environment = models.CharField(max_length=4, choices=ENV_CHOICES)
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Optional name or description for the connection")
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    DatabaseTNS = models.CharField(max_length=100)
    table_name = models.CharField(max_length=255, help_text="Enter desired table name")
    
    def __str__(self):
        return f"{self.environment} - {self.name if self.name else self.username}"
