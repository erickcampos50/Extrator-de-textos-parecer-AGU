import streamlit as st
import pandas as pd
import pdfplumber
import base64
import re
import tempfile

def extract_tables_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Inicializando um DataFrame vazio para armazenar todas as tabelas
        all_tables = pd.DataFrame()
        
        # Iterando através de cada página do PDF
        for page in pdf.pages:
            # Extraindo tabelas da página atual
            table = page.extract_table()
            
            # Convertendo a tabela em um DataFrame e concatenando com all_tables
            if table is not None:
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables = pd.concat([all_tables, df], ignore_index=True)
        
    return all_tables


# Funções previamente definidas
def extract_text_with_pdfplumber(file_path):
    with pdfplumber.open(file_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

def segment_topics_updated(text):
    pattern = re.compile(r'^(\d{1,3}\.\s)', re.MULTILINE)
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
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{encoded}" download="{filename}">Baixe a planilha Excel com os tópicos do parecer</a>'
    return href



# Página de extração de tabelas
def page_extract_tables():
    st.title('Extractor de Tabelas PDF')
    uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")
    if uploaded_file is not None:
        with st.spinner('Extraindo tabelas...'):
            with open("/tmp/temp.pdf", "wb") as f:
                f.write(uploaded_file.read())
            tables = extract_tables_from_pdf("/tmp/temp.pdf")
            st.success('Tabelas extraídas com sucesso!')
        st.dataframe(tables.head())
        if st.button('Baixar Tabelas como Excel'):
            towrite = io.BytesIO()
            tables.to_excel(towrite, index=False, engine='openpyxl')  
            towrite.seek(0)
            b64 = base64.b64encode(towrite.read()).decode()
            link = f'<a href="data:application/octet-stream;base64,{b64}" download="extracted_tables.xlsx">Baixar Excel</a>'
            st.markdown(link, unsafe_allow_html=True)

# Página de segmentação de tópicos
def page_segment_topics():
    st.title('Segmentador de Tópicos em PDF')
    st.write('Insira um parecer da AGU em PDF para converter a estrutura numa planilha')
    uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")
    if st.button('Segmentar Tópicos'):
        if uploaded_file is not None:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                    tmpfile.write(uploaded_file.read())
                    pdf_text = extract_text_with_pdfplumber(tmpfile.name)
                unwanted_term = "supersapiens.agu.gov.br/apps/tarefas/administrativo/minhas-tarefas/entrada/tarefa/"
                cleaned_text = remove_unwanted_lines(pdf_text, unwanted_term)
                segmented_topics = segment_topics_updated(cleaned_text)
                data = [[topic.split('.', 1)[0].strip(), topic.split('.', 1)[1].strip()] for topic in segmented_topics]
                df = pd.DataFrame(data, columns=['Número do tópico', 'Conteúdo'])
                st.dataframe(df)
                st.markdown("### Download da Planilha Excel")
                st.markdown(get_table_download_link(df), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Ocorreu um erro: {str(e)}")
        else:
            st.warning("Por favor, faça upload de um arquivo PDF.")

# Estrutura da aplicação com abas
st.sidebar.title("Navegação")
page = st.sidebar.radio("Escolha a página:", ('Segmentar Tópicos AGU','Extrair Tabelas de PDF'))

if page == 'Extrair Tabelas de PDF':
    page_extract_tables()
elif page == 'Segmentar Tópicos AGU':
    page_segment_topics()
