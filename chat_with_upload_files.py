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
    st.title("Alice's AI Agent #1 - Chat with CSV or PDF File")    

    user_upload = st.file_uploader("Upload your CSV or PDF file", type =["csv","pdf"])
  
    if user_upload is not None and user_upload.type not in ["text/csv","pdf"] : 
        st.write("Pleas upload a CSV or PDF file")
        
    if user_upload is not None and user_upload.type == "text/csv": 
        user_question = st.text_input("Ask a question about your CSV file: ") 
    
        agent = create_csv_agent(
            llm, user_upload, 
            verbose = True,
            allow_dangerous_code=True,
            return_intermediate_steps=True        
        )

        if user_question is not None and user_question !="":
            response = agent({"input": user_question})
            st.write(response["output"])
            st.divider()
            st.subheader("My thought process")
            st.markdown(response["intermediate_steps"][0][0])
            st.write(response["intermediate_steps"][0][1])
    
    if user_upload is not None and user_upload.type=="application/pdf": 
        temp_file = "./temp.pdf"
        with open(temp_file, "wb") as file:
            file.write(user_upload.getvalue())
            file_name = user_upload.name
            
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

