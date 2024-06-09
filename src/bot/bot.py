import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import os
import re
from utils import readUtil
from utils import writeUtil
from prompts import get_prompt, dict_prompt, get_additional_info_prompt
import json
from chat_interface import display_chat_interface

st.title("📝 PDFForm Filling ChatBot")
st.markdown("This is a user friendly PDFForm Filling ChatBot 😀")
st.sidebar.title("📝 PDFForm Filling ChatBot")
st.sidebar.markdown("This is a form filling assistant that uses OpenAI's GPT-3.5 language model to fill out forms.")

load_dotenv(find_dotenv())
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "context" not in st.session_state:
    st.session_state.context = []

def call_openai_language_model(messages):
    stream = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ],
        temperature=0.5,
        stream=True,
    )
    return stream

def call_openai_language_model_str_output(messages):
    response = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ],
        temperature=0
    )
    return response.choices[0].message.content

def is_json_serializable(data):
    try:
        json.loads(data)
        return True
    except json.JSONDecodeError:
        return False

def has_dictionary(input_string):
    start_index = input_string.find('{')
    end_index = input_string.rfind('}')

    return start_index != -1 and end_index != -1

def fix_missing_colons(dictionary_string):
    pattern = r'"([^"]+)":([^,}]+)'

    def add_colon(match):
        return f'"{match.group(1)}":{match.group(2)}'

    fixed_string = re.sub(pattern, add_colon, dictionary_string)

    return fixed_string

def extract_dictionary(input_string):
    start_index = input_string.find('{')
    end_index = input_string.rfind('}')
    dictionary_part = input_string[start_index:end_index+1]
    result = fix_missing_colons(dictionary_part)
    return result

def process_response(response):
    if has_dictionary(response):
        field_dict = readUtil.get_fields_dict(st.session_state.file_path)
        fields = list(field_dict.values())
        result = call_openai_language_model_str_output([{"role": "user", "content": dict_prompt(fields, response)}])
        final_details = json.loads(result)
        result = {}
        for key in field_dict:
            value = field_dict[key]
            if value in final_details:
                entry = final_details[value]
                result.update({key: entry})
        filepath = writeUtil.fill_pdf(result, st.session_state.file_path)
        st.session_state.conversation = None
        st.session_state.chat_history = None
        with open(filepath, 'rb') as f:
            st.download_button('Download Filled Form', f, file_name='filled_form_.pdf')
        st.write("Form filled successfully. Please download the filled form.")
        return True
    return False

if "file_upload_complete" not in st.session_state:
    pdf_form = st.sidebar.file_uploader("🗂️ Choose Your PDF Form", type=["pdf"], key="pdf_form")
    instructions_file = st.sidebar.file_uploader("📄 Choose additional instruction (Optional)", type=["docx", "doc"])
    submit_button = st.sidebar.button("Submit")

    instructions_text = ""
    doc_processed = False
    if submit_button:
        if instructions_file is not None:
            instructions_text = readUtil.extract_text_from_docx(instructions_file)
        doc_processed = True

    if pdf_form is not None and doc_processed:
        field_dict = readUtil.get_fields_dict(pdf_form)
        fields = list(field_dict.values())
        fields_dict = ""
        if instructions_text != "":
            fields_dict = call_openai_language_model_str_output([{"role": "system", "content": get_additional_info_prompt(fields, instructions_text)}])
        else:
            fields_dict = str({key: '' for key in fields})
        file_prompt = get_prompt(fields_dict)
        if file_prompt:
            st.session_state.context.append({"role": "system", "content": file_prompt})
            stream = call_openai_language_model_str_output(st.session_state.context)
            st.session_state.context.append({"role": "assistant", "content": stream})
            st.session_state.messages.append({"role": "assistant", "content": stream})
            st.session_state.file_upload_complete = True
            st.session_state.file_path = pdf_form
            st.session_state.instructions_file = instructions_file

if "file_upload_complete" in st.session_state and st.session_state.file_upload_complete and "start_conversation" in st.session_state:
    st.sidebar.markdown("**File has been submitted.**")

if "file_upload_complete" in st.session_state and st.session_state.file_upload_complete and "start_conversation" in st.session_state:
    display_chat_interface(st.session_state.messages, st.session_state.context, process_response, call_openai_language_model, st.session_state)

if "start_conversation" not in st.session_state and "file_upload_complete" in st.session_state and st.session_state.file_upload_complete:
    st.session_state.start_conversation = True
    st.button("Start Filling Form")