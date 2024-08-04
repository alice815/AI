import streamlit as st
import os
from PyPDF2 import PdfReader
from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.agents import create_csv_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core. messages import HumanMessage, AIMessage
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

def main():      
    load_dotenv()

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        max_tokens=10000,
        timeout=None,
        max_retries=2
    )
    
    st.set_page_config(page_title = "AI Agent")
    st.title("Alice's AI Agent")    

    user_csv = st.file_uploader("Upload your CSV file", type ="csv", key=1)
    user_pdf = st.file_uploader("Upload your PDF file", type ="pdf", key=2)

    if user_csv is not None:
        user_question = st.text_input("Ask a question about your csv file: ")

        agent = create_csv_agent(llm, user_csv, verbose = True,allow_dangerous_code=True)

        if user_question is not None and user_question !="":
            response = agent.run(user_question)
            st.write(response)

    if user_pdf is not None:
        temp_file = "./temp.pdf"
        with open(temp_file, "wb") as file:
            file.write(user_pdf.getvalue())
            file_name = user_pdf.name
            
        pdf_loader = PyPDFLoader(temp_file)
        pages = pdf_loader.load_and_split()

        text_splitter = CharacterTextSplitter(
            chunk_size = 5000,
            chunk_overlap = 600,
            length_function=len
        )
        context ="\n\n".join(str(p.page_content) for p in pages)
        chunks = text_splitter.split_text(context)

        embeddings = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
        vector_index = Chroma.from_texts(chunks, embeddings).as_retriever(search_kwargs={'k':5})
        
        user_question = st.text_input("Ask a question about your pdf file: ")

        
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            max_tokens=10000,
            timeout=None,
            max_retries=2
        )

        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever = vector_index,
            return_source_documents=False
        )

        if user_question is not None and user_question !="":
            response = qa_chain(user_question)
            st.write(response["result"])

if __name__ == "__main__":
    main()
