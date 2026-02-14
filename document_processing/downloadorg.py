from langchain_community.document_loaders import PyPDFLoader, CSVLoader, TextLoader, JSONLoader
import PyPDF2
import pandas as pd



def extract_PDF_Text(document):
    
    text_extract = ""
    with open(document,"rb") as f:
        documents = PyPDF2.PdfReader(f)
        for text in documents.pages:
            text_extract += text.extract_text()
    return text_extract

def extract_CSV_Text(document):
    text_extract = ""
    loader = CSVLoader(file_path=document)
    documents = loader.load()
    for text in documents:
        text_extract += text.page_content + "\n"
    return text_extract

def extract_Txt_text(document):
    text_extract = ""
    loader = TextLoader(file_path=document)
    documents = loader.load()
    for text in documents:
        text_extract += text.page_content
    return text_extract

def extract_Json_text(document):
    text_extract = ""
    loader = JSONLoader(file_path=document, jq_schema=".", text_content=False)
    documents = loader.load()
    for text in documents:
        text_extract += text.page_content
    return text_extract

def extract_Excel_text(document):
    text_extract = ""
    excel_file = pd.ExcelFile(document)

    for sheet in excel_file.sheet_names:
        df = pd.read_excel(document, sheet_name=sheet)
        text_extract += sheet
        for row in df.values:
            row_text = " | ".join(str(cell) for cell in row)
            text_extract += row_text
    return text_extract 


def extract_file_text(document):
    if document.lower().endswith(".pdf"):
        return extract_PDF_Text(document)
    elif document.lower().endswith(".csv"):
        return extract_CSV_Text(document)
    elif document.lower().endswith(".txt"):
        return extract_Txt_text(document)
    elif document.lower().endswith(".json"):
        return extract_Json_text(document)
    elif document.lower().endswith((".xls", ".xlsx")):
        return extract_Excel_text(document)
    else:

        raise ValueError(f"Unsupported file type: {document}")
