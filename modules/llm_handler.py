# modules/llm_handler.py
# This module handles the interaction with the Groq API.

import os
from dotenv import load_dotenv
import groq

load_dotenv()

# --- System Prompts ---
CONTEXTUAL_SYSTEM_PROMPT = """
You are a highly intelligent assistant with two primary functions: acting as an expert Amazon Athena SQL writer and as a general conversationalist. Your behavior is determined by the user's request and the context provided.

**CONTEXT:**
1.  **Conversation History:** The user's past messages are provided for context.
2.  **Database Schema:** The following Amazon Athena schema is available for you to use.

```sql
{schema}
```

**YOUR TASK:**
-   Analyze the user's latest prompt within the context of the conversation.
-   **If the prompt is a question that can be answered using the provided SQL schema, you MUST:**
    1.  Start your response with a friendly sentence, like "Of course, here is the Athena SQL query for your request:".
    2.  Generate the correct and efficient Amazon Athena (Presto SQL) query.
    3.  Wrap the SQL query in a markdown block like this: ```sql\\n[YOUR QUERY HERE]\\n```.
-   **If the prompt is a general question, a greeting, or unrelated to the schema, you MUST:**
    1.  Respond as a friendly and helpful conversational assistant.
    2.  Do NOT generate SQL or mention the schema unless the user asks about it.
-   **If the user asks for SQL but the schema is empty, you MUST:**
    1. Politely ask them to provide the schema in the sidebar first.
"""

GENERAL_SYSTEM_PROMPT = "You are a helpful and friendly conversational assistant. If the user asks for an SQL query, you MUST politely ask them to provide a database schema in the application's sidebar first."


# --- Core API Functions ---
def _get_groq_client(api_key: str) -> groq.Groq:
    """Initializes and returns a Groq API client."""
    client_api_key = api_key or os.getenv("GROQ_API_KEY")
    if not client_api_key:
        raise ValueError("Groq API Key not found. Please set a GROQ_API_KEY environment variable.")
    return groq.Groq(api_key=client_api_key)

def _call_groq_api(messages: list, api_key: str, model: str, temperature: float, max_tokens: int) -> str:
    """Makes a call to the Groq API and handles potential errors."""
    client = _get_groq_client(api_key)
    try:
        response = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, top_p=1,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
    except groq.RateLimitError:
        raise ConnectionError("Groq rate limit exceeded. Please check your plan.")
    except groq.AuthenticationError:
        raise ValueError("Authentication failed. Please check your Groq API key.")
    except groq.APIStatusError as e:
        raise RuntimeError(f"Groq API Error: {e.status_code} - {e.message}")
    except groq.APIConnectionError as e:
        raise ConnectionError(f"Failed to connect to Groq API: {e.__cause__}")


def get_available_models(api_key: str) -> list[str]:
    """Fetches the list of available model IDs from the Groq API."""
    client = _get_groq_client(api_key)
    models = client.models.list()
    # FIX: This now correctly returns all models without the '.active' filter
    return sorted([model.id for model in models.data])


def get_intelligent_response(chat_history: list, schema: str, api_key: str, model: str) -> str:
    """
    Determines user intent from history and context, providing an intelligent SQL or conversational response.
    """
    # If a schema is present, use the advanced contextual prompt.
    if schema and schema.strip():
        system_content = CONTEXTUAL_SYSTEM_PROMPT.format(schema=schema)
        temperature = 0.1
        max_tokens = 2000
    # Otherwise, use the simple general-purpose prompt.
    else:
        system_content = GENERAL_SYSTEM_PROMPT
        temperature = 0.7
        max_tokens = 1500

    messages = [{"role": "system", "content": system_content}]
    # Filter out any previous 'system' messages from history to avoid confusion
    messages.extend([msg for msg in chat_history if msg.get("role") != "system"])

    return _call_groq_api(messages, api_key, model, temperature, max_tokens)

