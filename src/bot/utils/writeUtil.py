from PyPDF2 import PdfReader, PdfWriter
import os

def fill_pdf(result, filename):
    reader = PdfReader(filename)
    writer = PdfWriter()

    blankTextFields = reader.get_form_text_fields()
    blankTextFieldsKeys = blankTextFields.keys()

    pdfFillerDict = {}
    pdfValueDict = result
    for key in blankTextFieldsKeys:
        if key in pdfValueDict:
            value = pdfValueDict[key]
            pdfFillerDict.update({key: value})

    writer.append(reader)

    for i in range(len(reader.pages)):
        writer.update_page_form_field_values(
            writer.pages[i], 
            pdfFillerDict
        )

    __dir__ = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(__dir__, "filled-out.pdf")

    with open(filepath, "wb") as output_stream:
        writer.write(output_stream)

    output_stream.close()
    return filepath