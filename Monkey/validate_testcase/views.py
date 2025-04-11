import requests
from django.shortcuts import render
from django.http import JsonResponse
from .forms import LogUploadForm
import re

# Function to parse log entries
def parse_log_entries(log_data):
    entries = []
    current_entry = None

    for line in log_data.splitlines():
        timestamp_match = re.match(r'^(\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) \[ (FromIso|ToIso|FromMC|ToMC)\:', line)
        if timestamp_match:
            if current_entry:
                entries.append(current_entry)
            current_entry = {
                'timestamp': timestamp_match.group(1),
                'direction': timestamp_match.group(2),
                'lines': [line],
                'in_lines': [],
                'out_lines': [],
            }
        elif current_entry:
            current_entry['lines'].append(line)
            if 'in[' in line:
                current_entry['in_lines'].append(line)
            elif 'out[' in line:
                current_entry['out_lines'].append(line)
    
    if current_entry:
        entries.append(current_entry)

    return entries

# Function to parse log data and send to API
def parse_log_data(log_data):
    url = 'http://localhost:8000/splunkparser/parse/'
    headers = {'Content-Type': 'application/json'}
    entries = parse_log_entries(log_data)
    
    combined_result = []

    for entry in entries:
        if entry['direction'] in ['FromIso', 'ToIso']:
            if entry['in_lines'] and entry['out_lines']:
                combined_result.append({
                    'timestamp': entry['timestamp'],
                    'direction': entry['direction'],
                    'result': {
                        'status': 'error',
                        'message': "Log input cannot contain both 'in[' and 'out[' lines. Use only one direction."
                    }
                })
            else:
                log_text = '\n'.join(entry['lines'])
                response = requests.post(url, headers=headers, json={'log_data': log_text})
                
                if response.status_code == 200:
                    result = response.json()
                    combined_result.append({
                        'timestamp': entry['timestamp'],
                        'direction': entry['direction'],
                        'result': result,
                    })

    return combined_result

# Function to parse log file content
def parse_log_file(file):
    content = file.read().decode('utf-8')
    return parse_log_data(content)

# View to handle log uploads
def upload_logs(request):
    form = LogUploadForm()
    result = None
    
    if request.method == 'POST':
        form = LogUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if 'file' in request.FILES:
                file = request.FILES['file']
                result = parse_log_file(file)
            else:
                log_data = form.cleaned_data['log_data']
                result = parse_log_data(log_data)
    
    return render(request, 'validate_testcase/index.html', {'form': form, 'result': result})
