from xhtml2pdf import pisa

def convert_html_to_pdf(source_html, output_pdf):
    result_file = open(output_pdf, "w+b")
    pisa_status = pisa.CreatePDF(source_html, dest=result_file)
    result_file.close()
    return pisa_status.err

with open("templates/cards/source.html", 'r') as file:
    source = "".join(file.readlines())
    print(source)
convert_html_to_pdf(source, "output.pdf")
