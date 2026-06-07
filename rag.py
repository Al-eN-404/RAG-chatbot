from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from retriever import retrieve

import os

load_dotenv()

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("API-KEY"),
    base_url="https://api.groq.com/openai/v1"
)

question = "What is transport?"

while True:

    question = input("\nAsk: ")

    if question.lower() == "exit":
        break
retrieved_chunks = retrieve(question)

content = "\n\n".join([chunk["text"] for chunk in retrieved_chunks])

prompt = f"""You are a helpful assistant.

Answer ONLY using the provided context.

Context:
{content}

Question:
{question}
"""

response = llm.invoke(prompt)
print(response.content)
