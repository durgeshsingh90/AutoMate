from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import os

# Assuming you have a function to handle the conversion
from .utils import convert_to_emvco

def upload_log(request):
    if request.method == 'POST' and request.FILES['log_file']:
        log_file = request.FILES['log_file']
        fs = FileSystemStorage()
        filename = fs.save(log_file.name, log_file)
        file_path = fs.path(filename)
        
        # Call the conversion function (you will implement the logic here)
        emvco_log = convert_to_emvco(file_path)
        
        # Save the converted file or return it directly in the response
        emvco_filename = os.path.splitext(filename)[0] + '_emvco.txt'
        emvco_file_path = fs.save(emvco_filename, emvco_log)
        emvco_file_url = fs.url(emvco_filename)
        
        return render(request, 'html2emvco/result.html', {'file_url': emvco_file_url})
    
    return render(request, 'html2emvco/upload.html')

def result_log(request):
    return render(request, 'html2emvco/result.html')
