# modules/rag_handler.py
# This module handles all the RAG (Retrieval-Augmented Generation) logic.

import pandas as pd
import io
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from .llm_handler import get_llm_chain

class RAGHandler:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.rag_chain = None
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def _load_and_process_file(self, uploaded_file) -> str:
        """Loads and processes the content of various file types into a single string."""
        try:
            if uploaded_file.type == "text/plain":
                return uploaded_file.getvalue().decode("utf-8")
            elif uploaded_file.type == "text/csv":
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                df = pd.read_excel(uploaded_file)
            else:
                raise ValueError(f"Unsupported file type: {uploaded_file.type}")

            output = io.StringIO()
            for col in df.columns:
                output.write(f"- Table/Sheet Name: '{col}'\n")
                output.write("  Columns:\n")
                for item in df[col].dropna():
                    output.write(f"    - {item}\n")
                output.write("\n")
            return output.getvalue()
        except Exception as e:
            raise RuntimeError(f"Failed to read or process file: {e}")

    def _create_rag_chain_from_content(self, content: str):
        """Private helper to build the RAG chain from a string content."""
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
        chunks = text_splitter.split_text(content)

        if not chunks:
            raise ValueError("Could not extract any text chunks from the provided content.")

        vectorstore = FAISS.from_texts(texts=chunks, embedding=self.embeddings)
        retriever = vectorstore.as_retriever()
        llm_chain = get_llm_chain(self.api_key, self.model)

        # --- UPDATE: The chain now takes a dictionary with context, question, and chat_history ---
        conversational_rag_chain = (
            RunnablePassthrough.assign(
                context=(lambda x: x["question"]) | retriever
            )
            | llm_chain
        )
        self.rag_chain = conversational_rag_chain

    def setup_rag_from_file(self, uploaded_file):
        file_content = self._load_and_process_file(uploaded_file)
        self._create_rag_chain_from_content(file_content)

    def setup_rag_from_text(self, text_content: str):
        self._create_rag_chain_from_content(text_content)
    
    # --- UPDATE: Added chat_history parameter and logic to format it ---
    def get_rag_response(self, question: str, chat_history: list) -> str:
        """Invokes the RAG chain to get a response for a given question."""
        if not self.rag_chain:
            raise ValueError("RAG chain is not initialized. Please process a schema first.")
        
        # Helper to format the chat history into a readable string
        def format_history(messages):
            if not messages:
                return "No conversation history."
            return "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages])

        formatted_history = format_history(chat_history)
        
        output_parser = StrOutputParser()
        final_chain = self.rag_chain | output_parser
        
        # --- UPDATE: The invoke call now passes the question and formatted history ---
        return final_chain.invoke({"question": question, "chat_history": formatted_history})

