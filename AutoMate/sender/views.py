# views.py
import os
import json
import logging
from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

logger = logging.getLogger('sender')  # Replace 'myapp' with your app name


def home(request):
    # Path to the schemes.json file inside the config folder
    json_file_path = os.path.join(settings.BASE_DIR, 'config', 'schemes.json')

    # Load the schemes.json file
    with open(json_file_path, 'r') as json_file:
        schemes_data = json.load(json_file)

    # Get the list of schemes from the JSON data
    schemes = schemes_data.get('schemes', [])

    # Pass the schemes to the template
    return render(request, 'sender/sender.html', {'schemes': schemes})  # Updated path

@csrf_exempt
def save_test_case(request):
    if request.method == 'POST':
        try:
            logger.debug("POST request received for saving test case")

            # Parse the request body
            data = json.loads(request.body)
            logger.debug(f"Request body: {data}")

            test_case_name = data.get('testCaseName', 'default_case')
            test_type = data.get('testType', 'default')
            content = data.get('content', '{}')

            logger.debug(f"Test Case Name: {test_case_name}, Test Type: {test_type}")
            logger.debug(f"Content to be saved: {content}")

            # Define the directory path where the test cases will be saved
            directory_path = os.path.join(settings.BASE_DIR,  'sender', 'testcases')

            logger.debug(f"Directory path: {directory_path}")

            # Ensure the directory exists
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
                logger.debug(f"Created directory: {directory_path}")

            # Create the full file path for the test case JSON
            file_path = os.path.join(directory_path, f'{test_case_name}.json')

            logger.debug(f"File path for test case: {file_path}")

            # Write the content to the file
            with open(file_path, 'w') as f:
                f.write(content)
                logger.debug(f"Successfully saved test case to {file_path}")

            return JsonResponse({'status': 'success'})

        except Exception as e:
            logger.error(f"Error saving test case: {str(e)}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    else:
        logger.warning(f"Invalid request method: {request.method}")
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
