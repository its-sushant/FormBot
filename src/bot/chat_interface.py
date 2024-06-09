import streamlit as st
import time

def display_chat_interface(messages, context, process_response, call_openai_language_model, session_state):
    session_timeout = False
    if "last_user_input_time" not in st.session_state:
        st.session_state.last_user_input_time = time.time()

    if time.time() - st.session_state.last_user_input_time > 60:
        session_state.clear()
        session_timeout = True
    
    if session_timeout:
        st.write("Session timed out. Please refresh the page to start a new session.")
        return
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if chat_prompt := st.chat_input("Type here..."):
        messages.append({"role": "user", "content": chat_prompt})
        with st.chat_message("user"):
            st.markdown(chat_prompt)
        context.append({"role": "user", "content": chat_prompt})
        stream = call_openai_language_model(context)
        response = st.write_stream(stream)
        processed = process_response(response)
        if processed:
            st.session_state.clear()
            return
        context.append({"role": "assistant", "content": response})
        messages.append({"role": "assistant", "content": response})
        st.session_state.last_user_input_time = time.time()