import streamlit as st
from PyPDF2 import PdfReader
import re
from io import BytesIO

st.set_page_config(page_title="ReglamentoBot - UNMdP", layout="wide")
st.title("🔍 ReglamentoBot - UNMdP")
st.caption("Sube tus PDFs de normativa y haz preguntas. El sistema busca fragmentos que contengan palabras clave de tu pregunta.")

# Subir archivos
uploaded_files = st.file_uploader("Sube tus documentos de reglamentación (PDF)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_text = ""
    sources = []
    for f in uploaded_files:
        reader = PdfReader(BytesIO(f.read()))
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        all_text += text
        sources.append(f.name)
    
    # Guardar en sesión
    st.session_state.full_text = all_text
    st.session_state.sources = sources
    st.success(f"✅ {len(uploaded_files)} documento(s) cargado(s).")

# Pregunta
pregunta = st.text_input("Haz una pregunta (ej: '¿Cuánto tiempo debe haber entre parciales?'):")
if pregunta and "full_text" in st.session_state:
    with st.spinner("Buscando fragmentos relevantes..."):
        # Limpiar y dividir texto en párrafos
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', st.session_state.full_text) if p.strip()]
        
        # Buscar párrafos que contengan alguna palabra clave de la pregunta
        palabras = [w.lower() for w in re.findall(r'\w{3,}', pregunta)]
        resultados = []
        for p in paragraphs:
            if any(w in p.lower() for w in palabras):
                resultados.append(p)
                if len(resultados) >= 5:  # máximo 5 fragmentos
                    break
        
        if resultados:
            st.subheader("📄 Fragmentos que contienen palabras clave:")
            for i, frag in enumerate(resultados):
                st.text_area(f"Fragmento {i+1}", frag[:1000] + ("..." if len(frag) > 1000 else ""), height=100)
                st.divider()
        else:
            st.warning("No se encontraron fragmentos con las palabras clave de tu pregunta.")
