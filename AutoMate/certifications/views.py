import os
import yaml
import json
from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse

def home(request):
    return render(request, 'certifications/home.html')

def load_test_cases(filename):
    yaml_file_path = os.path.join(settings.BASE_DIR, 'certifications', filename)
    with open(yaml_file_path, 'r') as file:
        return yaml.safe_load(file)

def save_test_cases(filename, data):
    yaml_file_path = os.path.join(settings.BASE_DIR, 'certifications', filename)
    with open(yaml_file_path, 'w') as file:
        yaml.safe_dump(data, file)

def testbook(request):
    cp_test_cases_data = load_test_cases('cardpresent.yaml')
    cnp_test_cases_data = load_test_cases('cardnotpresent.yaml')
    cp_folders = cp_test_cases_data.get('folders', [])
    cnp_folders = cnp_test_cases_data.get('folders', [])
    return render(request, 'certifications/testbook.html', {"cp_folders": cp_folders, "cnp_folders": cnp_folders})

def update_test_cases(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if 'cp_folders' in data:
            save_test_cases('cardpresent.yaml', {'folders': data['cp_folders']})
        if 'cnp_folders' in data:
            save_test_cases('cardnotpresent.yaml', {'folders': data['cnp_folders']})
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'}, status=400)

def build(request):
    return render(request, 'certifications/build.html')