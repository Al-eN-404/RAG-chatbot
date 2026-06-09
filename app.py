import streamlit as st
from rag import ask_rag
from scraper import crawl_website
from chunker import chunk_pages
from vectorstore import build_vectorstore


st.title("Website RAG Chatbot")

url = st.text_input(
    "Enter Website URL"
)

if "ready" not in st.session_state:
    st.session_state.ready = False


if st.button("Process Website"):

    status = st.empty()

    status.info("Scraping website...")

    pages = crawl_website(url)

    status.info("Chunking content...")

    chunks = chunk_pages(pages)

    st.write("Pages scraped:", len(pages))
    st.write("Chunks created:", len(chunks))

    if not chunks:
        st.error("No content found to index.")
        st.stop()

    status.info("Building vector database...")

    build_vectorstore(chunks)

    st.session_state.ready = True

    status.success("Knowledge base ready! You can now ask questions.")
    
question = st.text_input(
    "Ask a question",
    disabled=not st.session_state.ready
)
    
if (
    st.session_state.ready
    and st.button("Ask")
):

    result = ask_rag(
        question
    )

    st.subheader("Answer")

    st.write(
        result["answer"]
    )

    st.subheader("Sources")

    for source in result["sources"]:

        st.write(source)
# Updated final project code v2
