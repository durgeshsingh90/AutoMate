from django import forms
from .models import ServerConfig
from .models import YamlSchema

class ServerConfigForm(forms.ModelForm):
    class Meta:
        model = ServerConfig
        fields = ['name', 'hostname', 'port']

from django import forms
from .models import YamlSchema

class YamlSchemaForm(forms.ModelForm):
    class Meta:
        model = YamlSchema
        fields = ['schema_name', 'schema_content']
