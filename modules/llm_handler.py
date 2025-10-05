# modules/llm_handler.py
# This module handles the interaction with the Groq API.

import os
from dotenv import load_dotenv
import groq

# Load environment variables from a .env file for local development
load_dotenv()

def _call_groq_api(messages: list, api_key: str, model: str, temperature: float, max_tokens: int) -> str:
    """A private helper function to handle the core Groq API call."""
    client_api_key = api_key if api_key else os.getenv("GROQ_API_KEY")
    if not client_api_key:
        raise ValueError("Groq API Key not found. Please set a GROQ_API_KEY environment variable.")
    
    client = groq.Groq(api_key=client_api_key)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1,
    )
    
    # Safely handle potential None value from the API response
    content = response.choices[0].message.content
    return content.strip() if content else ""


def get_sql_query(prompt: str, api_key: str, model: str) -> str:
    """
    Calls the Groq API to generate an SQL query. Optimum values for temperature and tokens are set internally.

    Args:
        prompt (str): The fully constructed prompt with schema and user question.
        api_key (str): The API key for the Groq service, fetched from the environment.
        model (str): The model to use (e.g., 'llama3-70b-8192').

    Returns:
        str: The generated SQL query.
    """
    try:
        messages = [
            {"role": "system", "content": "You are an expert SQL developer specializing in Amazon Athena syntax. You ONLY respond with SQL code inside a markdown block. Do not add any explanation or conversational text."},
            {"role": "user", "content": prompt}
        ]
        
        # Optimum values for SQL generation
        temperature = 0.1
        max_tokens = 1000

        sql_query = _call_groq_api(messages, api_key, model, temperature, max_tokens)

        # Clean up the response to ensure it's just the SQL
        if sql_query.startswith("```sql"):
            sql_query = sql_query[7:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()

    except groq.APIConnectionError as e:
        raise ConnectionError(f"Failed to connect to Groq API: {e}")
    except groq.RateLimitError as e:
        raise ConnectionError(f"Rate limit exceeded. Please check your plan and usage: {e}")
    except groq.AuthenticationError as e:
        raise ValueError(f"Authentication failed. Please check your Groq API key: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


def get_general_response(prompt: str, api_key: str, model: str) -> str:
    """
    Calls the Groq API for a general conversational response.

    Args:
        prompt (str): The user's conversational prompt.
        api_key (str): The API key for the Groq service, fetched from the environment.
        model (str): The model to use.

    Returns:
        str: The conversational response.
    """
    try:
        messages = [
            {"role": "system", "content": "You are a helpful and friendly assistant. You can chat about various topics, but you also have a special skill: generating SQL queries for Amazon Athena if the user provides a database schema."},
            {"role": "user", "content": prompt}
        ]
        
        # Optimum values for conversation
        temperature = 0.7
        max_tokens = 1000

        return _call_groq_api(messages, api_key, model, temperature, max_tokens)

    except Exception as e:
        # Re-raise exceptions to be handled by the Streamlit app
        raise e

