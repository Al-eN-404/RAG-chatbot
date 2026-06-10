from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from retriever import retrieve

import os
# import content

load_dotenv()

def get_api_key():
    # Try multiple standard keys from streamlit secrets or env variables
    keys = ["API-KEY", "GROQ_API_KEY", "API_KEY", "OPENAI_API_KEY"]
    
    # 1. Try Streamlit Secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        for key in keys:
            if key in st.secrets:
                return st.secrets[key]
    except Exception:
        pass
        
    # 2. Try environment variables (for local deployment / env files)
    for key in keys:
        val = os.getenv(key)
        if val:
            return val
            
    return None

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=get_api_key(),
    base_url="https://api.groq.com/openai/v1"
)



def ask_rag(question):

    retrieved_chunks = retrieve(question)

    context = "\n\n".join(
        chunk["text"]
        for chunk in retrieved_chunks
    )
    
    sources=list({
        chunk["url"]
        for chunk in retrieved_chunks
    })

    prompt = f"""
    Answer ONLY using the provided context.

    Context:
    {context}

    Question:
    {question}
    """

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": sources
    }

# updated final version..
    
