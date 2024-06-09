from pypdf import PdfReader
from docx import Document

def get_fields_detail(filename):
    reader = PdfReader(filename)
    fields = reader.get_fields()
    return fields

def get_fields_dict(reference_form):
    ref_fields = get_fields_detail(reference_form)
    field_dict = {}
    count = 0
    for key in ref_fields:
        value = ref_fields[key]
        if value.get('/TU') == 'RadioButtonList' or value.get('/TU') is None:
            continue
        else:
            field_dict[value.get('/T')] = value.get('/TU')
    return field_dict

def extract_text_from_docx(filepath):
    document = Document(filepath)
    full_text = ""
    for paragraph in document.paragraphs:
        full_text += paragraph.text + "\n"
    return full_text