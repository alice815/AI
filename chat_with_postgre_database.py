import os
from dotenv import load_dotenv

import streamlit as st
import psycopg2

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import GoogleGenerativeAI

load_dotenv()

#Setup database connection
db_user=os.getenv("sql_user")
db_pw=os.getenv("sql_password")
db_host=os.getenv("db_host")
db_port= "5432"
db_="hass_db"

pg_uri = f"postgresql+psycopg2://{db_user}:{db_pw}@{db_host}:{db_port}/{db_}"
db = SQLDatabase.from_uri(pg_uri,schema="public", view_support=True)

#Setup the model
def get_sql_chain(db):
    template = """
        You are a data analyst and interact with a user who is asking questions about a smart home database. 
        Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.
        
        <SCHEMA>{schema}</SCHEMA>
    
        Converstation History: {chat_history}
    
        Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks.
    
        For example:
        Question: how many temperature sensors in the database?
        SQL Query: SELECT count(entity_id) FROM public.states_meta WHERE entity_id like 'sensor.%temperature'; 
        question: name all the motion sensors
        SQL Query: SELECT entity_id FROM public.states_meta WHERE entity_id like 'binary_sensor.%motion';
    
        Your turn:
        Question: {question}
        SQL Query:
        """
    
    prompt=ChatPromptTemplate.from_template(template)

    llm=GoogleGenerativeAI(model="gemini-1.5-flash") 

    def get_schema(_):
        return db.get_table_info()

    return(
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )

def get_response(user_query: str, db: SQLDatabase, chat_history: list):
    sql_chain = get_sql_chain(db)

    template="""
    You are a data analyst. You are interact with a user who is aksing you question about the company's database.
    Base on the table schema below, question, sql query, and sql response, write a natural lanuguage response.
    <SCHEMA>{schema}</SCHEMA>

    Conversation History: {chat_history}
    SQL Query: <SQL>{query}</SQL>
    User Question: {question}
    SQL Response: {response}
    """

    prompt=ChatPromptTemplate.from_template(template)

    llm=GoogleGenerativeAI(model="gemini-1.5-flash") 

    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema=lambda _: db.get_table_info(),
            response = lambda vars: db.run(vars["query"]),
        )
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain.invoke({
        "question": user_query,
        "chat_history": chat_history,
})

#Setup user interface
st.set_page_config(page_title="SQL_Agent")
st.title("Chat with Smart Home Database")

if "chat_history" not in st.session_state:
    st.session_state.chat_history=[
        AIMessage(content ="Hello! I am a SQL assistant. Ask me anything about your smart home database.")
    ]

for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)
            
user_query = st.chat_input("Type a message...")
if user_query is not None and user_query.strip() != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    with st.chat_message("Human"):
        st.markdown(user_query)

    with st.chat_message("AI"):
        sql_chain = get_sql_chain(db)
        response_1 = sql_chain.invoke({
            "chat_history": st.session_state.chat_history,
            "question": user_query
        })            
        st.markdown(response_1)        
    
        response = get_response(user_query, db, st.session_state.chat_history)
        st.markdown(response)

    st.session_state.chat_history.append(AIMessage(content=response))

