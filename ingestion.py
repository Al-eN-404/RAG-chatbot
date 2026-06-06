import langchain
import requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

print("Everything works!")
load_dotenv()



import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("API-KEY"),
    base_url="https://api.groq.com/openai/v1")

response = llm.invoke("Explain RAG simply")
print(response.content)