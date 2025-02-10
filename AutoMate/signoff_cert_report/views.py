from django.shortcuts import render
from django.views import View
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.http import HttpResponse
import fitz  # PyMuPDF
import logging
import os
import json
from datetime import datetime

# Get the logger
logger = logging.getLogger('django')

class PDFUploadView(View):
    def get(self, request):
        return render(request, 'signoff_cert_report/upload.html')

    def post(self, request):
        if 'pdf_files' not in request.FILES:
            return HttpResponse("No files selected.", status=400)
        
        pdf_files = request.FILES.getlist('pdf_files')
        num_files = len(pdf_files)
        logger.info(f'Number of files being uploaded: {num_files}')
        
        storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        all_text = ""
        all_extracted_info = []
        
        for index, pdf_file in enumerate(pdf_files):
            logger.info(f'Processing file {index + 1}/{num_files}: {pdf_file.name}')
            # Save the file temporarily
            filename = storage.save(pdf_file.name, pdf_file)
            pdf_path = storage.path(filename)
            pdf_text = self.convert_pdf_to_text(pdf_path)
            all_text += f"Filename: {pdf_file.name}\n\n{pdf_text}\n\n"
            extracted_info = self.extract_info(pdf_text)
            all_extracted_info.append({pdf_file.name: extracted_info})
            # Delete the file after processing
            storage.delete(filename)

        # Create a text file with the combined text and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        combined_text_filename = f'combined_text_{timestamp}.txt'
        text_file_content = ContentFile(all_text.encode('utf-8'))
        output_filepath = storage.save(combined_text_filename, text_file_content)
        self.log_info(all_text, all_extracted_info)

        # Extract JSON data
        json_data = self.extract_json_data(all_extracted_info)
        
        # Render the final output with JSON data only
        return render(request, 'signoff_cert_report/json_data.html', {
            'json_data': json.dumps(json_data, indent=4, ensure_ascii=False),  # Format JSON for pretty print
        })

    def convert_pdf_to_text(self, pdf_path):
        pdf_document = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text


    def extract_info(self, text):
        fields = [
            'Company Name', 'Acquiring Institution', 'Street', 'Post Code and City',
            'Phone Number', 'Contact person', 'E-Mail Address', 'Terminal Type / Host Type',
            'Software version', 'Termid'
        ]
        
        # Split the text into lines
        lines = text.split('\n')

        found_fields = {}
        values = {}
        collect_values = False
        current_field = None
        collecting_street = False
        collecting_phone_number = False
        collecting_contact_person = False

        skipped_lines = []

        for index, line in enumerate(lines):
            line = line.strip()

            if not line:
                if collecting_phone_number and index > 0:
                    previous_line = lines[index - 1].strip()
                    if previous_line and not any(previous_line.startswith(field) for field in fields):
                        values['Phone Number'] = previous_line
                        collecting_phone_number = False
                if collecting_contact_person and index < len(lines) - 1:
                    next_line = lines[index + 1].strip()
                    for skipped_line in skipped_lines:
                        logger.info("Starts")
                        logger.info(f"Skipped line for 'Contact person:': {skipped_line}")
                    if next_line:
                        logger.info(f"'Contact person:' found, value: {next_line}")
                        values['Contact person'] = next_line
                        collecting_contact_person = False
                    skipped_lines.clear()

                collect_values = False
                current_field = None
                collecting_street = False
                continue

            if collect_values and current_field:
                # For Street field, collect until an empty line appears or 'Post Code and City' line is found
                if current_field == 'Street':
                    if line.startswith('Post Code and City') or line.startswith('Phone Number'):
                        collecting_street = False
                    else:
                        values[current_field] = values.get(current_field, '') + ' ' + line
                        collecting_street = True
                else:
                    values[current_field] = values.get(current_field, '') + ' ' + line
                    collect_values = False
                    current_field = None
                continue

            for field in fields:
                if line.startswith(field):
                    current_field = field
                    found_fields[field] = True
                    value = line[len(field):].strip().lstrip(':').strip()  # Clean value
                    if value:
                        values[field] = value
                        collect_values = False
                        current_field = None
                        collecting_street = False
                    else:
                        if field == 'Phone Number':
                            collecting_phone_number = True
                        elif field == 'Contact person':
                            logger.info(f"'Contact person:' field found, beginning to collect skipped lines")
                            collecting_contact_person = True
                            skipped_lines = []
                        collect_values = True
                    break

            if collecting_contact_person:
                skipped_lines.append(line)

        # If still collecting street data, continue until an empty line
        if collecting_street:
            street_value_lines = []
            while index < len(lines):
                line = lines[index].strip()
                index += 1
                if not line or line.startswith('Post Code and City') or line.startswith('Phone Number'):
                    break
                street_value_lines.append(line)
            if street_value_lines:
                values['Street'] = ' '.join(street_value_lines).strip()

        # Find 'Post Code and City' if not found and check one line before 'Phone Number'
        if 'Post Code and City' not in values:
            for i, line in enumerate(lines):
                if line.startswith('Phone Number') and i > 0:
                    values['Post Code and City'] = lines[i - 1].strip()
                    break

        # Format the values, remove leading/trailing whitespace
        for key in values.keys():
            values[key] = values[key].strip()

        # Handle missing fields
        for field in fields:
            if field not in values:
                values[field] = 'Not Found'

        return values


    def log_info(self, pdf_text, extracted_info):
        logger.debug("PDF Text: %s", pdf_text)
        logger.debug("Extracted Info: %s", extracted_info)

    def extract_json_data(self, extracted_info):
        json_data = []
        for info in extracted_info:
            for filename, data in info.items():
                json_data.append({
                    'filename': filename,
                    'company_name': data.get('Company Name', 'Not Found'),
                    'acquiring_institution': data.get('Acquiring Institution', 'Not Found'),
                    'street': data.get('Street', 'Not Found'),
                    'post_code_and_city': data.get('Post Code and City', 'Not Found'),
                    'phone_number': data.get('Phone Number', 'Not Found'),
                    'contact_person': data.get('Contact person', 'Not Found'),  # Added 'Contact person'
                    # 'email_address': data.get('E-Mail Address', 'Not Found'),  # Added 'E-Mail Address'
                    # 'terminal_type_host_type': data.get('Terminal Type / Host Type', 'Not Found'),  # Added 'Terminal Type / Host Type'
                    # 'software_version': data.get('Software version', 'Not Found'),  # Added 'Software version'
                    # 'termid': data.get('Termid', 'Not Found'),  # Added 'Termid'
                })
        return json_data
