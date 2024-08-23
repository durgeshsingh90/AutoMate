import os
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from .forms import LogFileForm
from lxml import etree

def find_online_message_parent(elem):
    if elem.tag == 'OnlineMessage':
        return elem
    elif elem.getparent() is None:
        return None
    else:
        return find_online_message_parent(elem.getparent())

def search_and_copy(xml_file, search_strings, output_file):
    tree = etree.parse(xml_file)
    root = tree.getroot()

    for elem in root.iter():
        if elem.text is not None:
            for search_string in search_strings:
                if search_string in elem.text:
                    online_message_parent = find_online_message_parent(elem)
                    if online_message_parent is not None:
                        output_file.write(etree.tostring(online_message_parent).decode())
                        output_file.write('\n')
                        break

def copy_xml_sections(xml_file, output_file_path, search_strings):
    with open(xml_file, 'r') as xml_file_reader, open(output_file_path, 'w') as f_out:
        for _ in range(2):
            line = xml_file_reader.readline()
            f_out.write(line)

        in_section = False

        for line in xml_file_reader:
            if "<LogDetails>" in line or "<ConnectionList>" in line:
                in_section = True
                f_out.write(line)
            elif "</LogDetails>" in line or "</ConnectionList>" in line:
                in_section = False
                f_out.write(line)
            elif in_section:
                f_out.write(line)

        f_out.write("<OnlineMessageList>\n")
        search_and_copy(xml_file, search_strings, f_out)
        f_out.write("</OnlineMessageList>\n")

        lines = xml_file_reader.readlines()
        if lines:
            last_line = lines[-1]
            f_out.write(last_line)

def copy_last_line(input_file, output_file):
    with open(input_file, 'r') as input_file_reader:
        last_line = input_file_reader.readlines()[-1]

    with open(output_file, 'a') as output_file_writer:
        output_file_writer.write(last_line)

def process_log_file(log_file_path, rrn_numbers):
    search_strings = rrn_numbers.strip().split('\n')
    output_file_path = log_file_path.split('.')[0] + "_output.xml"
    copy_xml_sections(log_file_path, output_file_path, search_strings)
    copy_last_line(log_file_path, output_file_path)
    return output_file_path

def upload_log_file(request):
    if request.method == 'POST':
        form = LogFileForm(request.POST, request.FILES)
        if form.is_valid():
            log_file = request.FILES['log_file']
            rrn_numbers = form.cleaned_data['rrn_numbers']

            # Save the uploaded file to the server
            fs = FileSystemStorage()
            log_file_path = fs.save(log_file.name, log_file)
            log_file_path = fs.path(log_file_path)

            # Process the log file
            output_file_path = process_log_file(log_file_path, rrn_numbers)

            # Pass the file paths to the template for feedback
            context = {
                'form': form,
                'output_file_path': output_file_path,
                'log_file_path': log_file_path,
                'file_saved': True
            }
            return render(request, 'mclogsfilter/upload.html', context)
    else:
        form = LogFileForm()

    return render(request, 'mclogsfilter/upload.html', {'form': form})
