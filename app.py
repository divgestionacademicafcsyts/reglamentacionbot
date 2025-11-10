import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import tempfile
import os

st.set_page_config(page_title="ReglamentoBot - UNMdP", layout="wide")
st.title("🔍 ReglamentoBot - UNMdP")
st.caption("Sube tus PDFs de normativa y haz preguntas. Solo se usa lo que subas.")

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

uploaded_files = st.file_uploader("Sube tus documentos (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Procesando documentos..."):
        texts = []
        for f in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(f.read())
                reader = PdfReader(tmp.name)
                text = "".join(page.extract_text() or "" for page in reader.pages)
                texts.append(text)
                os.unlink(tmp.name)

        # Dividir en fragmentos
        splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        chunks = splitter.split_text("\n\n".join(texts))

        # Crear embeddings ligeros
        try:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            vectorstore = FAISS.from_texts(chunks, embeddings)
            st.session_state.vectorstore = vectorstore
            st.success("✅ Documentos cargados y listos para consultas.")
        except Exception as e:
            st.error(f"Error al crear la base: {e}")
            st.session_state.vectorstore = None

# Pregunta
pregunta = st.text_input("Haz una pregunta sobre la reglamentación:")
if pregunta and st.session_state.vectorstore:
    with st.spinner("Buscando..."):
        docs = st.session_state.vectorstore.similarity_search(pregunta, k=3)
        for i, doc in enumerate(docs):
            st.markdown(f"**Fragmento {i+1}**")
            st.text(doc.page_content[:1000] + ("..." if len(doc.page_content) > 1000 else ""))
            st.divider()
elif pregunta and not st.session_state.vectorstore:
    st.warning("Primero sube al menos un PDF.")
