# app.py
# Main Streamlit application file

import streamlit as st
import os
from dotenv import load_dotenv
from pathlib import Path
from modules.llm_handler import get_available_models
from modules.rag_handler import RAGHandler
import base64

# Load environment variables from project .env explicitly
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)

# --- Page Configuration ---
st.set_page_config(
    page_title="Athena RAG Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- Helper function to load and encode the logo ---
def get_image_as_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Logo not found at path: {path}.")
        return None

# --- UI Styling (Full CSS) ---
st.markdown("""
<style>
    .stCodeBlock {
        background-color: #2E2E2E;
        color: #FFFFFF;
        border-radius: 10px;
        padding: 1rem;
        font-family: 'Courier New', Courier, monospace;
    }
    .stButton>button {
        border-radius: 10px;
    }
    .main-title-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .logo-img {
        width: 80px;
        height: 80px;
        pointer-events: none;
    }
    .main-title-container h1 {
        margin: 0;
    }
    .stChatInput {
        position: relative;
        overflow: visible;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 25px;
        padding: 1px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 4px 8px rgba(0,0,0,0.6), 0 2px 0 rgba(255,255,255,0.02) inset;
        transition: transform 180ms ease, box-shadow 180ms ease;
    }
    .stChatInput::before {
        content: "";
        position: absolute;
        top: -1px;
        left: 9px;
        right: 9px;
        height: 6px;
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
        background: linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0));
        filter: blur(5px);
        opacity: 0.85;
        pointer-events: none;
        z-index: 2;
        transition: background 180ms ease, filter 180ms ease, opacity 180ms ease;
    }
    .stChatInput:focus-within {
        box-shadow: 0 4px 20px rgba(0,0,0,0.65), 0 0 30px rgba(0,175,255,0.18);
    }
    .stChatInput:focus-within::before {
        background: linear-gradient(180deg, rgba(0,175,255,0.20), rgba(255,255,255,0));
        filter: blur(8px);
        opacity: 1;
    }
    .stTextArea textarea, .stTextInput input, div[role="textbox"] {
        background: transparent !important;
        color: #E6EEF8;
        border: none;
        outline: none;
        resize: vertical;
    }
    .stButton>button {
        box-shadow: 0 4px 8px rgba(0,0,0,0.6), 0 2px 0 rgba(255,255,255,0.02) inset;
        background: #232323;
        color: #fff;
        border: none;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background: #232323;
        box-shadow: 0 0 10px #00afff, 0 6px 16px rgba(0,175,255,0.12);
        transition: box-shadow 180ms ease, transform 120ms ease;
    }
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stInfo,
    [data-testid="stSidebar"] .stFileUploader {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 16px;
        padding: 10px 12px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 4px 8px rgba(0,0,0,0.6), 0 2px 0 rgba(255,255,255,0.02) inset;
        margin-bottom: 10px;
    }
    
    [data-testid="stSidebar"] .stTextArea {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 20px;
        padding: 10px 10px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 4px 4px rgba(0,0,0,0.6), 0 2px 0 rgba(255,255,255,0.02) inset;
        margin-bottom: 10px;
    }
    
    [data-testid="stSidebar"] .stSelectbox:focus-within,
    [data-testid="stSidebar"] .stInfo:focus-within,
    [data-testid="stSidebar"] .stFileUploader:focus-within {
        box-shadow: 0 4px 8px rgba(0,0,0,0.65), 0 2px 20px rgba(0,175,255,0.18);
    }
    [data-testid="stSidebar"] .stTextArea:focus-within {
        box-shadow: 0 4px 4px rgba(0,0,0,0.65), 0 2px 6px rgba(0,175,255,0.18);
    }
    
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #E6EEF8;
    }
</style>
""", unsafe_allow_html=True)

# --- Helper function to process schema from file or text ---
def process_schema(content, is_file=False):
    """Initializes RAG handler and processes schema from file or text."""
    with st.spinner("Processing schema... This may take a moment."):
        try:
            st.session_state.rag_handler = RAGHandler(
                api_key=st.session_state.api_key,
                model=st.session_state.selected_model
            )
            if is_file:
                st.session_state.rag_handler.setup_rag_from_file(content)
            else:
                st.session_state.rag_handler.setup_rag_from_text(content)
            st.success("Successfully processed schema.", icon="✅")
        except Exception as e:
            st.error(f"Error processing schema: {e}", icon="🚫")
            if "rag_handler" in st.session_state:
                del st.session_state.rag_handler

# --- Sidebar for Configuration ---
with st.sidebar:
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("GROQ_API_KEY") or (st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None)

    model_options = []
    if st.session_state.api_key:
        try:
            model_options = get_available_models(st.session_state.api_key)
        except Exception as e:
            st.error(f"Failed to fetch models: {e}", icon="🚫")
    else:
        st.warning("Please add your GROQ_API_KEY to the .env file.", icon="⚠️")

    st.subheader("⚙️ Model Settings")
    st.session_state.selected_model = st.selectbox("Select Groq Model", model_options, index=model_options.index("openai/gpt-oss-120b") if "openai/gpt-oss-120b" in model_options else 0, disabled=not model_options)

    st.subheader("📄 Database Schema")
    
    tab1, tab2 = st.tabs(["Upload File", "Paste Schema"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Upload schema file",
            type=["txt", "csv", "xlsx"],
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            if st.session_state.get("processed_input_id") != uploaded_file.name:
                process_schema(uploaded_file, is_file=True)
                st.session_state.processed_input_id = uploaded_file.name

    with tab2:
        schema_text = st.text_area(
            "Paste schema here",
            height=250,
            label_visibility="collapsed",
            placeholder="CREATE TABLE customers(...);"
        )
        if st.button("Submit Schema"):
            if schema_text and schema_text.strip():
                if st.session_state.get("processed_input_id") != schema_text:
                    process_schema(schema_text, is_file=False)
                    st.session_state.processed_input_id = schema_text
            else:
                st.warning("Please paste some schema text before processing.", icon="⚠️")

# --- Main Chat Interface ---
logo_path = "Picsart_25-10-06_09-13-30-411.png"
logo_base64 = get_image_as_base64(logo_path)
if logo_base64:
    st.markdown(f'<div class="main-title-container"><img src="data:image/jpeg;base64,{logo_base64}" class="logo-img"><h1>Athena RAG Assistant</h1></div>', unsafe_allow_html=True)
else:
    st.title("🤖 Athena RAG Assistant")

st.markdown("Provide your database schema in the sidebar to begin generating SQL queries.")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! Please provide your database schema in the sidebar to get started."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about your data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.api_key:
        st.error("Please set your GROQ_API_KEY in your environment (.env file or Streamlit secrets).")
    elif "rag_handler" not in st.session_state:
        st.warning("Please provide a schema in the sidebar before asking a question.", icon="⚠️")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Searching schema and thinking..."):
                try:
                    # --- UPDATE: Pass the entire message history to the RAG handler ---
                    response_content = st.session_state.rag_handler.get_rag_response(
                        question=prompt, 
                        chat_history=st.session_state.messages
                    )
                    st.markdown(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})

                except Exception as e:
                    error_message = f"An error occurred: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

