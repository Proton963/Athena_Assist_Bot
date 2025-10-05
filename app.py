# app.py
# Main Streamlit application file

import streamlit as st
import os
import base64
from dotenv import load_dotenv
from pathlib import Path
from modules.llm_handler import get_sql_query, get_general_response
from config import PROMPT_TEMPLATE
import re

# Load environment variables from project .env explicitly
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)

# --- Page Configuration ---
st.set_page_config(
    page_title="Athena & Chat Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- Helper function to load and encode the logo ---
def get_image_as_base64(path):
    """Reads an image file and returns its base64 encoded string."""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except FileNotFoundError:
        return None

# --- UI Styling ---
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
    
    /* Custom styles for the title and logo */
    .main-title-container {
        display: flex;
        align-items: center;
        gap: 15px; /* Adjust space between logo and text */
    }
    .logo-img {
        width: 100px;
        height: 100px;
        pointer-events: none; /* Makes the image non-clickable */
    }
    .main-title-container h1 {
        margin: 0; /* Remove default margin from h1 */
    }

    /* Elevated input / chat box wrapper (.stTextInput, .stTextArea)*/ 
    /* Targets Streamlit text input/textarea and chat input container */
    .stChatInput {
        position: relative;
        overflow: visible;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 25px;
        padding: 1px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 8px 15px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.02) inset;
        transition: transform 180ms ease, box-shadow 180ms ease;
    }

    /* Faint white glowing/top border to simulate light on the top edge */
    .stChatInput::before {
        content: "";
        position: absolute;
        top: -2px;
        left: 9px;
        right: 9px;
        height: 6px;
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
        background: linear-gradient(180deg, rgba(255,255,255,0.16), rgba(255,255,255,0));
        filter: blur(6px);
        opacity: 0.85;
        pointer-events: none;
        z-index: 2;
        transition: background 180ms ease, filter 180ms ease, opacity 180ms ease;
    }

    /* Slight lift on focus with colored glow (#00afff) */
    .stChatInput:focus-within {
        box-shadow: 0 8px 15px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.02) inset;
        box-shadow:
            0 12px 300px rgba(0,0,0,0.65),
            0 0 40px rgba(0,175,255,0.18); /* subtle outer blue glow */
    }

    /* Intensify the top glow and tint it with the accent color on focus */
    .stChatInput:focus-within::before {
        background: linear-gradient(180deg, rgba(0,175,255,0.20), rgba(255,255,255,0));
        filter: blur(8px);
        opacity: 1;
    }

    /* Make inner text area transparent so the wrapper handles the background */
    .stTextArea textarea, .stTextInput input, div[role="textbox"] {
        background: transparent !important;
        color: #E6EEF8;
        border: none;
        outline: none;
        resize: vertical;
    }

    /* Style the send/submit button to match elevated look */
    .stButton>button {
        box-shadow: 0 6px 16px rgba(0,175,255,0.12);
        background: linear-gradient(90deg,#00afff,#4C6FFF);
        color: #fff;
        border: none;
    }

    /* New: Sidebar elevated boxes - match the main chat input look */
    /* Targets Streamlit sidebar container and common widgets inside it */
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stInfo {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 16px;
        padding: 10px 12px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 8px 8px rgba(0,0,0,0.6), 0 2px 0 rgba(255,255,255,0.02) inset;
        transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
        margin-bottom: 18px;
    }
    
    [data-testid="stSidebar"] .stTextArea {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border-radius: 16px;
        padding: 10px 12px;
        border: 1px solid rgba(255,255,255,0.04);
        box-shadow: 0 8px 10px rgba(0,0,0,0.6), 0 2px 0 rgba(255,255,255,0.02) inset;
        transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
        margin-bottom: 18px;
    }

    /* Focus / hover lift + subtle blue glow */
    [data-testid="stSidebar"] .stSelectbox:focus-within,
    [data-testid="stSidebar"] .stInfo:focus-within {
        box-shadow:
            0 12px 30px rgba(0,0,0,0.65),
            0 0 20px rgba(0,175,255,0.18);
    }
    
    [data-testid="stSidebar"] .stTextArea:focus-within {
        box-shadow:
            0 8px 10px rgba(0,0,0,0.65),
            0 0 20px rgba(0,175,255,0.18);    
                    
    }

    /* Make inner inputs transparent so the wrapper handles the visual style */
    [data-testid="stSidebar"] .stTextArea textarea,
    [data-testid="stSidebar"] .stSelectbox select,
    [data-testid="stSidebar"] div[role="textbox"] {
        background: transparent !important;
        color: #E6EEF8;
        border: none;
        outline: none;
        resize: vertical;
    }

    /* Sidebar labels / small text color */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #E6EEF8;
    }

    /* Keep the info box icon/emoji visible and consistent */
    # [data-testid="stSidebar"] .stInfo {
    #     display: block;
    #     padding: 12px;
    # }

    /* Small spacing tweak so components look like separate cards */
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stTextArea {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def is_sql_request(text: str) -> bool:
    """
    A simple heuristic to determine if a prompt is asking for an SQL query.
    Looks for common SQL-related keywords.
    """
    # Use regex to find keywords, case-insensitive, as whole words
    sql_keywords = [
        r'\bselect\b', r'\bfrom\b', r'\bwhere\b', r'\bjoin\b', r'\bgroup by\b',
        r'\bfind\b', r'\bshow me\b', r'\blist all\b', r'\bget me\b',
        r'\bquery\b', r'\bdatabase\b', r'\btable\b', r'\bcustomers\b', r'\busers\b',
        r'\borders\b', r'\bdata\b', r'\bcount\b', r'\bsum\b', r'\bavg\b'
    ]
    # Combine keywords into a single regex pattern
    pattern = re.compile('|'.join(sql_keywords), re.IGNORECASE)
    return bool(pattern.search(text))


# --- Sidebar for Configuration ---
with st.sidebar:
    
    # Prefer session-stored API key, otherwise check environment and Streamlit secrets
    if "api_key" not in st.session_state:
        env_key = os.getenv("GROQ_API_KEY") or (st.secrets.get("GROQ_API_KEY") if hasattr(st, "secrets") else None)
        st.session_state.api_key = env_key

    st.subheader("Model Settings")
    model_options = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile"]
    selected_model = st.selectbox("Select Groq Model", model_options, index=0) # Default to gpt

    st.subheader("Database Schema (for SQL)")
    schema_text = st.text_area(
        "Paste your Athena table schema here...",
        height=250,
        placeholder="CREATE TABLE customers (\n  id INT,\n  name VARCHAR(255),\n  signup_date DATE\n);"
    )
    
    # st.info("💡 Provide a schema only when you want to generate SQL queries.", icon="ℹ️")


# --- Main Chat Interface ---
logo_path = "D:/Athena Ai Chatbot/Picsart_25-10-05_20-22-13-175.png"  # Make sure this image is in the same folder as app.py
logo_base64 = get_image_as_base64(logo_path)

if logo_base64:
    st.markdown(
        f"""
        <div class="main-title-container">
            <img src="data:image/jpeg;base64,{logo_base64}" class="logo-img" alt="logo">
            <h1>Athena & Chat Assistant</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    # Fallback if the logo is not found
    st.title("🤖 Athena & Chat Assistant")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "Hello! How can I help you today? You can ask me a general question, or add your database schema in the sidebar to ask for an SQL query."
    }]

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Pre-flight checks ---
    if not st.session_state.api_key:
        st.error("Please set your GROQ_API_KEY in the .env file to continue.")
    else:
        # Determine the type of request
        is_sql_query_request = is_sql_request(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    if is_sql_query_request:
                        if not schema_text:
                            response_content = "It looks like you're asking for an SQL query. Please provide your database schema in the sidebar first!"
                            st.warning(response_content)
                        else:
                            # Construct the full prompt for the LLM
                            full_prompt = PROMPT_TEMPLATE.format(
                                schema=schema_text,
                                question=prompt
                            )
                            generated_sql = get_sql_query(
                                prompt=full_prompt,
                                api_key=st.session_state.api_key,
                                model=selected_model
                            )
                            response_content = f"Here is the Athena SQL query for your request:\n\n```sql\n{generated_sql}\n```"
                            st.markdown(response_content)
                    else:
                        # It's a general conversation request
                        response_content = get_general_response(
                            prompt=prompt,
                            api_key=st.session_state.api_key,
                            model=selected_model
                        )
                        st.markdown(response_content)
                    
                    # Add the final response to history
                    st.session_state.messages.append({"role": "assistant", "content": response_content})

                except Exception as e:
                    error_message = f"An error occurred: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

