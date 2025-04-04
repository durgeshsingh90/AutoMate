from django.http import JsonResponse
import os
import json
import zipfile
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .scripts.astrex_html_logfilter.breakhtml_1 import run_breakhtml
from .scripts.astrex_html_logfilter.adjusthtml_2 import run_adjusthtml
from .scripts.astrex_html_logfilter.unique_de32_html_3 import run_unique_de32_html

def index(request):
    folder = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if filename.endswith(('.html', '.json', '.zip', '.xml')):
                file_path = os.path.join(folder, filename)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

    return render(request, 'astrex_html_logs/index.html')

@csrf_exempt
def upload_log(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            uploaded_file = request.FILES['file']
            filename = uploaded_file.name.lower()

            upload_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs')
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, uploaded_file.name)

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            if filename.endswith('.html'):
                run_breakhtml(file_path)
                run_adjusthtml(file_path)
                run_unique_de32_html(file_path, max_processes=10)

                de032_result = run_unique_de32_html(file_path, max_processes=10)

                return JsonResponse({
                    'status': 'success',
                    'message': f'File {uploaded_file.name} uploaded and processed successfully.',
                    'filename': uploaded_file.name,
                    'de032_counts': de032_result.get("consolidated_de032_value_counts", {}),
                    'execution_time': de032_result.get("execution_time", {}),
                    'total_count': de032_result.get("total_DE032_count", 0)
                })


            return JsonResponse({'status': 'error', 'message': 'Only .html files are supported.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

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
                    zipf.write(file_path, os.path.relpath(file_path, settings.MEDIA_ROOT))

            return JsonResponse({'status': 'success', 'zip_file': f"astrex_html_logs/{os.path.basename(zip_path)}"})
        else:
            return JsonResponse({'status': 'error', 'message': 'Filtered files not ready'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@csrf_exempt
def download_filtered_by_de032(request):
    if request.method == 'POST':
        try:
            de032_value = request.POST.get('de032')
            filename = request.POST.get('filename')  # original .html filename

            if not de032_value or not filename:
                return JsonResponse({'status': 'error', 'message': 'Missing DE032 or filename'})

            json_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', 'unique_bm32.json')

            from .scripts.astrex_html_logfilter.astrex_html_filter_4 import run_astrex_html_filter
            run_astrex_html_filter(json_path, [de032_value])  # DE032 value as condition list

            base_name = os.path.splitext(filename)[0]
            filtered_file = f"{base_name}_filtered_{de032_value}.html"
            filtered_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', filtered_file)

            if os.path.exists(filtered_path):
                return JsonResponse({
                    'status': 'success',
                    'filtered_file': f"astrex_html_logs/{filtered_file}"
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Filtered file not found.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
