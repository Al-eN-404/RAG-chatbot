import streamlit as st
from rag import ask_rag


st.title("Website RAG Chatbot")

url = st.text_input(
    "Enter Website URL"
)

question = st.text_input(
    "Ask a question"
)

if st.button("Process Website"):

    st.write("Scraping website...")
    
if st.button("Ask"):

    answer = ask_rag(question)

    st.write(answer)
