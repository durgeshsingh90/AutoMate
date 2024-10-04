import os
import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import logging

# Initialize logger
logger = logging.getLogger('sender')  # Replace 'sender' with your app name

# Path where the test cases (JSON files) are stored
TEST_CASES_DIR = os.path.join(settings.BASE_DIR, 'sender', 'static', 'sender', 'testcases')
print(TEST_CASES_DIR)  # Add this line temporarily to see the path in the console

def home(request):
    """
    View to render the homepage with the Monaco editor.
    """
    return render(request, 'sender/sender.html')  # Render the HTML page

def get_json_files(request):
    """
    View to recursively list all files and folders in the testcases folder.
    """
    try:
        def get_folder_structure(directory):
            # Recursively get folder structure with files
            folder_structure = {}
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    # If it's a directory, recursively get its contents
                    folder_structure[item] = get_folder_structure(item_path)
                elif item.endswith('.json'):
                    # If it's a JSON file, add it to the structure
                    folder_structure[item] = None
            return folder_structure
        
        folder_structure = get_folder_structure(TEST_CASES_DIR)
        return JsonResponse(folder_structure, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@csrf_exempt  # Allow saving without CSRF protection (you can add it back later)
def save_json(request, filename):
    """
    View to save the edited JSON file.
    """
    if request.method == 'POST':
        file_path = os.path.join(TEST_CASES_DIR, filename)
        if not os.path.exists(file_path) or not filename.endswith('.json'):
            return JsonResponse({'error': 'Invalid file'}, status=400)

        try:
            json_data = json.loads(request.body)
            with open(file_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=2)
            return JsonResponse({'message': 'File saved successfully'})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# TEST_CASES_DIR = os.path.join(settings.BASE_DIR, 'AutoMate', 'sender', 'static', 'sender', 'testcases')

@csrf_exempt
def create_folder(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            folder_name = data.get('folderName')
            new_folder_path = os.path.join(TEST_CASES_DIR, folder_name)

            # Create the new folder
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': 'Folder already exists!'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
def move_file(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_path = os.path.join(TEST_CASES_DIR, data.get('filePath'))
            target_folder_path = os.path.join(TEST_CASES_DIR, data.get('targetFolderPath'))

            # Ensure the target folder exists
            if not os.path.exists(target_folder_path):
                return JsonResponse({'success': False, 'message': 'Target folder does not exist'}, status=400)

            # Move the file
            if os.path.exists(file_path):
                new_path = os.path.join(target_folder_path, os.path.basename(file_path))
                os.rename(file_path, new_path)
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': 'File does not exist'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
