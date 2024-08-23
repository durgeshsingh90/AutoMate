import os
from django.core.management.base import BaseCommand
from sender.models import YamlSchema

class Command(BaseCommand):
    help = 'Load initial YAML schema'

    def handle(self, *args, **kwargs):
        schema_path = os.path.join(os.path.dirname(__file__), 'omnipay_len_cnfg.yaml')
        with open(schema_path, 'r') as file:
            schema_content = file.read()
            if not YamlSchema.objects.exists():
                YamlSchema.objects.create(schema_content=schema_content)
                self.stdout.write(self.style.SUCCESS('Successfully loaded initial schema'))
    