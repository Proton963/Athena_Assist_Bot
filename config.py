# config.py
# Stores configuration constants and prompt templates.

PROMPT_TEMPLATE = """
Based on the Amazon Athena table schema below, write a compatible SQL query that answers the user's question.

**Instructions:**
1.  Your response must be ONLY the SQL query. Do not include any explanations, comments, or markdown formatting like ```sql.
2.  Ensure the SQL syntax is specifically for **Amazon Athena (Presto SQL)**.
3.  Pay close attention to data types and column names from the provided schema.

**Schema:**
```sql
{schema}
```

**User's Question:**
"{question}"

**SQL Query:**
"""
