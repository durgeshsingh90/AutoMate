from django.shortcuts import render, redirect
from .forms import ServerConfigForm, YamlSchemaForm
from .models import ServerConfig, YamlSchema
import yaml
import socket

def home(request):
    servers = ServerConfig.objects.all()
    schema = YamlSchema.objects.first()
    return render(request, 'sender/home.html', {'servers': servers, 'schema': schema})

def server_config(request):
    if request.method == 'POST':
        form = ServerConfigForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sender:home')
    else:
        form = ServerConfigForm()
    return render(request, 'sender/server_config.html', {'form': form})

def send_transaction(request, server_id):
    if request.method == 'POST':
        data = request.POST['data']
        server_config = ServerConfig.objects.get(id=server_id)
        schema = YamlSchema.objects.first()

        response = ""
        try:
            yaml.safe_load(data)
        except yaml.YAMLError as e:
            return render(request, 'sender/home.html', {'response': f'YAML validation error: {str(e)}', 'servers': ServerConfig.objects.all(), 'schema': schema})

        if server_config:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((server_config.ip_address, server_config.port))
                s.sendall(data.encode())
                response = s.recv(1024).decode()

        return render(request, 'sender/home.html', {'response': response, 'servers': ServerConfig.objects.all(), 'schema': schema})
    return redirect('sender:home')

def yaml_schema_config(request):
    schema = YamlSchema.objects.first()
    if request.method == 'POST':
        form = YamlSchemaForm(request.POST, instance=schema)
        if form.is_valid():
            form.save()
            return redirect('sender:home')
    else:
        form = YamlSchemaForm(instance=schema)
    return render(request, 'sender/yaml_schema_config.html', {'form': form, 'schema': schema.schema_content})

from django.http import JsonResponse
import os
import json


def get_field_definitions(request):
    file_path = os.path.join(os.path.dirname(__file__), 'config', 'omnipay_fields_definitions.json')
    with open(file_path, 'r') as file:
        data = json.load(file)
    return JsonResponse(data)
