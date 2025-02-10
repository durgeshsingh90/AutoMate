from django.shortcuts import render
from PyPDF2 import PdfMerger
from django.http import HttpResponse
import io

def merge_pdfs(request):
    if request.method == 'POST':
        pdf_files = request.FILES.getlist('pdf_files')
        file_order = request.POST.get('file_order')

        if not pdf_files or not file_order:
            return render(request, 'pdf_merger/merge_pdfs.html', {'error': 'No files were uploaded or file order is missing.'})
        
        order = list(map(int, file_order.split(',')))  # Convert to a list of integers
        ordered_files = [pdf_files[i] for i in order]

        merger = PdfMerger()
        for pdf in ordered_files:
            merger.append(pdf)

        merged_pdf = io.BytesIO()
        merger.write(merged_pdf)
        merger.close()
        merged_pdf.seek(0)

        response = HttpResponse(merged_pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="merged.pdf"'
        return response

    return render(request, 'pdf_merger/merge_pdfs.html')
