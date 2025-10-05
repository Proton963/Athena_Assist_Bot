# app.py
# Main Streamlit application file

import streamlit as st
import os
from dotenv import load_dotenv
from pathlib import Path
from modules.llm_handler import get_intelligent_response, get_available_models
import base64
import sys

# Load environment variables from project .env explicitly
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)

sys.path.insert(0, str(Path(__file__).parent))

# --- Page Configuration ---
st.set_page_config(
    page_title="Athena & Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- Initialize Session State ---
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GROQ_API_KEY") or (st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None)
if "schema_text" not in st.session_state:
    st.session_state.schema_text = ""
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you? To generate SQL, please add your schema in the sidebar."}]


# --- Helper function to load and encode the logo ---
def get_image_as_base64(path):
    """Reads an image file and returns its base64 encoded string."""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"Logo not found at path: {path}. Please ensure the image is in the same directory as the app.")
        return None

# --- UI Styling (FIX: Restored the complete CSS) ---
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
        background: linear-gradient(90deg,#00afff,#4C6FFF);
        box-shadow: 0 0 10px #00afff, 0 6px 16px rgba(0,175,255,0.12);
        transition: box-shadow 180ms ease, transform 120ms ease;
    }

    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stInfo,
    [data-testid="stSidebar"] .stTextArea {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 16px;
        padding: 10px 12px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 4px 8px rgba(0,0,0,0.6), 0 2px 0 rgba(255,255,255,0.02) inset;
        margin-bottom: 10px;
    }
    [data-testid="stSidebar"] .stSelectbox:focus-within,
    [data-testid="stSidebar"] .stInfo:focus-within,
    [data-testid="stSidebar"] .stTextArea:focus-within {
        box-shadow: 0 4px 8px rgba(0,0,0,0.65), 0 2px 20px rgba(0,175,255,0.18);
    }
    [data-testid="stSidebar"] .stTextArea textarea,
    [data-testid="stSidebar"] .stSelectbox select,
    [data-testid="stSidebar"] div[role="textbox"] {
        background: transparent !important;
        color: #E6EEF8;
        border: none;
        outline: none;
        resize: vertical;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #E6EEF8;
    }
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stTextArea {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# --- Sidebar for Configuration ---
with st.sidebar:
    model_options = []
    if st.session_state.api_key:
        try:
            model_options = get_available_models(st.session_state.api_key)
        except Exception as e:
            st.error(f"Failed to fetch models: {e}", icon="🚫")
    else:
        st.warning("Please add your GROQ_API_KEY to the .env file.", icon="⚠️")

    st.subheader("Model Settings")
    default_index = model_options.index("gemma2-9b-it") if "gemma2-9b-it" in model_options else 0
    selected_model = st.selectbox("Select Groq Model", model_options, index=default_index, disabled=not model_options)

    st.subheader("Database Schema (for SQL)")
    schema_input = st.text_area(
        "Paste your Athena table schema here...", 
        height=250, 
        placeholder="CREATE TABLE customers( \nid INT, \nname VARCHAR(255), \nsignup_date DATE \n); ",
        value=st.session_state.schema_text
    )

    if st.button("Submit Schema", key="submit_schema"):
        st.session_state.schema_text = schema_input
        st.success("Schema submitted and active.", icon="✅")
    
    if st.session_state.schema_text:
        st.info("A schema is active. The assistant will now prioritize generating SQL.", icon="ℹ️")


# --- Main Chat Interface ---
logo_path = "Picsart_25-10-05_20-22-13-175.png"
logo_base64 = get_image_as_base64(logo_path)
if logo_base64:
    st.markdown(f'<div class="main-title-container"><img src="data:image/jpeg;base64,{logo_base64}" class="logo-img"><h1>Athena & Chat Assistant</h1></div>', unsafe_allow_html=True)
else:
    st.title("🤖 Athena & Chat Assistant")

st.markdown("Ask a general question or provide a schema in the sidebar to generate an Athena SQL query.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.api_key:
        st.error("Please set your GROQ_API_KEY in your environment (.env file or Streamlit secrets).")
    elif not selected_model:
        st.error("Model selection is not available. Please check your API key.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response_content = get_intelligent_response(
                        chat_history=st.session_state.messages,
                        schema=st.session_state.schema_text,
                        api_key=st.session_state.api_key,
                        model=selected_model
                    )

                    st.markdown(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})

                except Exception as e:
                    error_message = f"An error occurred: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

