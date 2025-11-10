# app.py
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import tempfile
import os

st.set_page_config(page_title="ReglamentoBot - UNMdP", layout="wide")
st.title("🔍 ReglamentoBot - UNMdP")
st.caption("Asistente de normativa administrativa – Sube tus PDFs y haz preguntas")

# Inicializar estado de sesión
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "docs_loaded" not in st.session_state:
    st.session_state.docs_loaded = False

# Subida de archivos
uploaded_files = st.file_uploader(
    "Sube tus documentos de reglamentación (PDF)",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files and not st.session_state.docs_loaded:
    with st.spinner("Procesando documentos..."):
        docs = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            loader = PyPDFLoader(tmp_path)
            docs.extend(loader.load())
            os.unlink(tmp_path)

        if docs:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)

            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                model_kwargs={'device': 'cpu'}
            )
            vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
            
            st.session_state.vectorstore = vectorstore
            st.session_state.docs_loaded = True
            st.success(f"✅ {len(uploaded_files)} documento(s) cargado(s) y listo(s) para consultas.")

if not st.session_state.docs_loaded:
    st.info("Por favor, sube al menos un PDF para comenzar.")
    st.stop()

# Campo de pregunta
pregunta = st.text_input("🔍 Haz una pregunta sobre la reglamentación:")
if pregunta:
    with st.spinner("Buscando en la normativa..."):
        retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 3})
        resultados = retriever.invoke(pregunta)
        
        if resultados:
            st.subheader("📄 Fragmentos relevantes:")
            for i, doc in enumerate(resultados):
                st.markdown(f"**Fragmento {i+1}**")
                st.text(doc.page_content)
                st.caption(f"Fuente: Archivo subido")
                st.divider()
        else:
            st.warning("No se encontraron fragmentos relevantes en los documentos cargados.")
