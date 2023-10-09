import streamlit as st
import pandas as pd
import pdfplumber
import re
import tempfile
import base64


# Funções previamente definidas
def extract_text_with_pdfplumber(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

def segment_topics_updated(text):
    pattern = re.compile(r'^(\d+\.)', re.MULTILINE)
    matches = list(pattern.finditer(text))
    segments = []
    for i in range(len(matches)):
        start = matches[i].start()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        segments.append(text[start:end].strip())
    return segments

def remove_unwanted_lines(text, unwanted_term):
    lines = text.split('\n')
    cleaned_lines = [line for line in lines if unwanted_term not in line]
    cleaned_text = '\n'.join(cleaned_lines)
    return cleaned_text

# Função para baixar o DataFrame como um arquivo Excel
def get_table_download_link(df, filename="data.xlsx"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmpfile:
        df.to_excel(tmpfile.name, index=False)
        with open(tmpfile.name, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{encoded}" download="{filename}">Baixe a planilha Excel</a>'
    return href

# Código Streamlit
st.title('Segmentador de Tópicos em PDF')
uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if st.button('Segmentar Tópicos'):
    if uploaded_file is not None:
        try:
            # Extraindo e limpando o texto
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                tmpfile.write(uploaded_file.read())
                pdf_text = extract_text_with_pdfplumber(tmpfile.name)
            unwanted_term = "supersapiens.agu.gov.br/apps/tarefas/administrativo/minhas-tarefas/entrada/tarefa/"
            cleaned_text = remove_unwanted_lines(pdf_text, unwanted_term)
            
            # Segmentando os tópicos e criando um DataFrame
            segmented_topics = segment_topics_updated(cleaned_text)
            data = [[topic.split('.', 1)[0].strip(), topic.split('.', 1)[1].strip()] for topic in segmented_topics]
            df = pd.DataFrame(data, columns=['Topic Number', 'Topic Content'])
            
            # Mostrando os tópicos na interface
            st.dataframe(df)
            
            # Download da planilha Excel
            st.markdown("### Download da Planilha Excel")
            st.markdown(get_table_download_link(df), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Ocorreu um erro: {str(e)}")
    else:
        st.warning("Por favor, faça upload de um arquivo PDF.")
