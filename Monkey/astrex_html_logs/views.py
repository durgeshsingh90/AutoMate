from django.http import JsonResponse
import os
import json
import zipfile
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from threading import Thread

from .scripts.astrex_unique_de32_html import extract_de032_counts_from_html
from .scripts.astrex_html_filter import filter_html_by_conditions
from .scripts.html2emvco import convert_html_to_emvco


def index(request):
    folder = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if filename.endswith(('.html', '.json', '.zip', '.xml')):  # added .xml
                file_path = os.path.join(folder, filename)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

    return render(request, 'astrex_html_logs/index.html')

@csrf_exempt
def upload_log(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()

        # Set upload path
        upload_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs')
        os.makedirs(upload_path, exist_ok=True)

        file_path = os.path.join(upload_path, uploaded_file.name)

        # Save the uploaded file
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # If HTML file — extract DE032 and filter
        if filename.endswith('.html'):
            de032_counts, unique_count, start_time, end_time, key = extract_de032_counts_from_html(file_path)

            Thread(
                target=run_filter_for_each_de032,
                args=(file_path, de032_counts),
                daemon=True
            ).start()

            return JsonResponse({
                'status': 'success',
                'message': f'File {uploaded_file.name} uploaded and processed successfully.',
                'unique_count': unique_count,
                'de032_counts': de032_counts,
                'start_time': start_time,
                'end_time': end_time,
                'key': key,
                'filename': uploaded_file.name
            })

        return JsonResponse({'status': 'error', 'message': 'Only .html or .xml files are allowed.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})



def run_filter_for_each_de032(html_file_path, de032_counts):
    filtered_files = []
    for de032_value in de032_counts.keys():
        conditions = [de032_value]
        output_file = filter_html_by_conditions(html_file_path, conditions)
        if output_file:
            filtered_files.append(output_file)

    # Save all filtered file paths to a progress file (JSON)
    progress_file = os.path.splitext(html_file_path)[0] + "_progress.json"
    with open(progress_file, 'w') as f:
        json.dump(filtered_files, f)
    
def check_filter_progress(request):
    html_file_name = request.GET.get('filename')
    if not html_file_name:
        return JsonResponse({'status': 'error', 'message': 'Filename not provided'})

    progress_file = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', f"{os.path.splitext(html_file_name)[0]}_progress.json")

    if os.path.exists(progress_file):
        with open(progress_file) as f:
            filtered_files = json.load(f)
            filtered_files = [os.path.relpath(path, settings.MEDIA_ROOT) for path in filtered_files]
        return JsonResponse({'status': 'success', 'files': filtered_files})
    else:
        return JsonResponse({'status': 'processing'})

@csrf_exempt
def zip_filtered_files(request):
    if request.method == 'POST':
        filename = request.POST.get('filename')
        if not filename:
            return JsonResponse({'status': 'error', 'message': 'Filename not provided'})

        progress_file = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', f"{os.path.splitext(filename)[0]}_progress.json")

        if os.path.exists(progress_file):
            with open(progress_file) as f:
                filtered_files = json.load(f)
            zip_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', f"{os.path.splitext(filename)[0]}_filtered_all.zip")

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_path in filtered_files:
                    zipf.write(file_path, os.path.relpath(file_path, settings.MEDIA_ROOT))  # relative path

            return JsonResponse({'status': 'success', 'zip_file': f"astrex_html_logs/{os.path.basename(zip_path)}"})
        else:
            return JsonResponse({'status': 'error', 'message': 'Filtered files not ready'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@csrf_exempt
def convert_to_emvco(request):
    if request.method == 'POST':
        filename = request.POST.get('filename')
        if not filename:
            return JsonResponse({'status': 'error', 'message': 'Filename not provided'})

        input_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', filename)
        output_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', f"{os.path.splitext(filename)[0]}_emvco.xml")

        success = convert_html_to_emvco(input_path, output_path)

        if success and os.path.exists(output_path):
            return JsonResponse({'status': 'success', 'output_file': f"astrex_html_logs/{os.path.basename(output_path)}"})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to generate EMVCo log.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
