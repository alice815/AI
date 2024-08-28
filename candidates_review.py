import time
import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
import win32com.client
from IPython.display import Markdown, display

#Load job description
job_pdf=PyPDFLoader('filepath/JobDescription.pdf')
job_docs=job_pdf.load()
job=[d.page_content for d in job_docs]
job_requirement=json.dumps(job)

#Load candidates resume
resume_pdf=PyPDFLoader('filepath/candidate.pdf')
resume_docs=resume_pdf.load()
resume=[d.page_content for d in resume_docs]
resume=json.dumps(resume)

#Load API key
load_dotenv()
GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

#Create Model
generation_config = {
    "temperature": 0.4,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 10000,
    "response_mime_type": "text/plain"    
}

prompt = ("""
    I am looking for --- to join my team.
    Please review candidates resume and write a summary of the candidate's experiences. 
    Please compare the resume and job requirement to identify matches and gaps. 
    Please rank the candidates based on how well they meet the job requirements with a scale of 1–10, with 10 being the perfrect match. 
    Please use the resume and job requirement that I provided, do not make things up.
    Please start your response with the candidate name on first line.
    """ )

chat = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": [job_requirement, resume],
    }
  ]
)

#Get result
chat.send_message(candidate_analysis_prompt)
Markdown(chat.last.text)

#email result to myself
outlook = win32com.client.Dispatch('Outlook.Application')
response=chat.last.text
mail = outlook.CreateItem(0)
mail.To = os.getenv('MY_EMAIL')
mail.Subject = response.partition('\n')[0]
mail.Body = str(response)
mail.Send()

