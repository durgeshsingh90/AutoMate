# AutoMate\sender\models.py
from django.db import models

class ServerConfig(models.Model):
    name = models.CharField(max_length=100)
    hostname = models.CharField(max_length=255, default='default_hostname')  # Provide a sensible default
    port = models.IntegerField()

    def __str__(self):
        return self.name

from django.db import models

class YamlSchema(models.Model):
    schema_name = models.CharField(max_length=100, default='Default Schema')
    schema_content = models.TextField()

    def __str__(self):
        return self.schema_name
