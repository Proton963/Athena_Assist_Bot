# modules/llm_handler.py
# This module handles the interaction with the Groq API and prompt templating for LangChain.

import os
from dotenv import load_dotenv
import groq
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import SecretStr

load_dotenv()

# --- System Prompts ---
# --- UPDATE: Added chat_history to the prompt template ---
RAG_PROMPT_TEMPLATE = """
You are an expert Amazon Athena (Presto SQL) writer. Your goal is to write a correct and efficient SQL query based on the user's question, the provided schema context, and the ongoing conversation.

**CONVERSATION HISTORY:**
{chat_history}

**SCHEMA CONTEXT:**
Here is the relevant schema information retrieved from the user's document. Use this to understand the tables and columns available.
{context}

**RULES:**
1.  Use the conversation history to understand context from previous messages (e.g., pronouns like "it" or "that").
2.  Generate ONLY the Amazon Athena (Presto SQL) query that answers the NEW QUESTION below.
3.  Do not add any extra explanations, greetings, or conversational text.
4.  Wrap the final SQL query in a markdown block like this: ```sql\\n[YOUR QUERY HERE]\\n```.
5.  **IMPORTANT:** When creating table aliases, you MUST NOT use the letter 'e' as an alias.

**NEW QUESTION:**
{question}

**SQL QUERY:**
"""


# --- Core API Functions ---
def _get_groq_client(api_key: str) -> groq.Groq:
    """Initializes and returns a Groq API client."""
    client_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not client_api_key:
        raise ValueError("Groq API Key not found. Please set a GROQ_API_KEY.")
    return groq.Groq(api_key=client_api_key)

def get_available_models(api_key: str) -> list[str]:
    """Fetches the list of available model IDs from the Groq API."""
    client = _get_groq_client(api_key)
    models = client.models.list()
    return sorted([model.id for model in models.data])

def get_llm_chain(api_key: str, model: str):
    """
    Creates and returns a LangChain chain with the Groq model and a prompt template.
    """
    llm = ChatGroq(temperature=0, api_key=SecretStr(api_key), model=model)
    
    # --- UPDATE: Added chat_history to input_variables ---
    prompt = PromptTemplate(
        template=RAG_PROMPT_TEMPLATE,
        input_variables=["chat_history", "context", "question"]
    )
    
    return prompt | llm

