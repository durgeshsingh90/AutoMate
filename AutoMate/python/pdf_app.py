import PyPDF2

def extract_pages(input_pdf, output_pdf, start_page, end_page):
    with open(input_pdf, 'rb') as pdf_file:
        # Create a PDF reader object
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)

        # Check if the chosen end page exceeds the number of pages of the pdf file
        if end_page >= pdf_reader.numPages:
            end_page = pdf_reader.numPages - 1

        # Create a PDF writer object
        pdf_writer = PyPDF2.PdfFileWriter()

        # Add the specified page range to the writer object
        for page_num in range(start_page, end_page + 1):
            page = pdf_reader.getPage(page_num)
            pdf_writer.addPage(page)

        # Write the pages to the output PDF
        with open(output_pdf, 'wb') as output_pdf_file:
            pdf_writer.write(output_pdf_file)

input_pdf_path = 'input.pdf'  # Path to the original PDF
output_pdf_path = 'output.pdf'  # Path to save the extracted pages
start_page = 10  # Start page (0-indexed, this is page 11 in human-readable terms)
end_page = 20  # End page (0-indexed, this is page 21 in human-readable terms)

extract_pages(input_pdf_path, output_pdf_path, start_page, end_page)
