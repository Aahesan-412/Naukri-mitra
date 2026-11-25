import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

MODEL_NAME = "openai/gpt-oss-120b"

def get_llm():
    return ChatGroq(
        model=MODEL_NAME,
        temperature=0.2
    )
