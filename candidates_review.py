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
    "max_output_tokens": 100000,
    "response_mime_type": "text/plain"    
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

## Analyze Job Description
    job_posting_analysis_prompt = ("""
        I am looking for --- to join my team. 
        Could you please review the job description and breakdown the key skills, qualifications, and experiences required""")
    chat = model.start_chat(
      history=[
        {
          "role": "user",
          "parts": [job_requirement],
        }
      ]
    )
    chat.send_message(job_posting_analysis_prompt)
    Markdown(chat.last.text)

## Review Individaul Candidates in a folder
    file = 'path/candidate.pdf'
    resume_pdf=PyPDFLoader(file)
    resume_docs=resume_pdf.load()
    resume=[d.page_content for d in resume_docs]
    resume=json.dumps(resume)
    candidate_review_prompt = ("""
        I am looking for --- to join my team.
        Please review candidates resume and write a summary of the candidate's experiences. 
        Please compare the resume and job requirement to identify matches and gaps. 
        Please rank the candidates based on how well they meet the job requirements with a scale of 1–10, with 10 being the perfrect match. 
        Please provide the reasoning of why you think the candidates are good match. 
        Please use the candidate name as your subject.
        Please use the  job requirement and resumes that I provided, do not make things up.
        """ )
    #load Resume and Job Description
    chat = model.start_chat(
      history=[
        {
          "role": "user",
          "parts": [job_requirement, resume]
        }
      ]
    )
    chat.send_message(candidate_review_prompt)
    response=chat.last.text
    Markdown(response)
    #email result to myself
    outlook = win32com.client.Dispatch('Outlook.Application')
    response=chat.last.text
    mail = outlook.CreateItem(0)
    mail.To = os.getenv('MY_EMAIL')
    mail.Subject = response.partition('\n')[0]
    mail.Body = str(response)
    mail.Send()

## Compare All Candidates
    #Load all resumes
    files = glob.glob('path/*.pdf')
    resumes=[]
    
    for file in files:
        resume_pdf=PyPDFLoader(file)
        resume_docs=resume_pdf.load()
        resume=[d.page_content for d in resume_docs]
        resume=json.dumps(resume)
        resumes.append(resume)
    resumes_all=json.dumps(resumes)
    candidate_review_prompt = ("""
        I am the business performance analytics manager and looking for a Business Performance Analyst III to join my team.
        Please review candidates resume and write a summary of the candidate's experiences. 
        Please compare the resume and job requirement to identify matches and gaps. 
        Please rank the candidates based on how well they meet the job requirements with a scale of 1–10, with 10 being the perfrect match. 
        Please use the  job requirement and resume that I provided, do not make things up.
        Please include below information in your response and in a table format with each candidate in a seperate row:
        Name
        Location
        Email
        overal rating
        Summary
        Match
        Gap
        Power BI skill
        SQL skill
        Data Analytic skill
        Communication skill
        Collaboration skill
        Recommendation    
        """ )
    
    chat = model.start_chat(
      history=[
        {
          "role": "user",
          "parts": [job_requirement, resumes_all],
        }
      ]
    )
    
    #Get result
    chat.send_message(candidate_review_prompt)
    Markdown(chat.last.text)
    
    #email result to myself
    outlook = win32com.client.Dispatch('Outlook.Application')
    response=chat.last.text
    mail = outlook.CreateItem(0)
    mail.To = os.getenv('MY_EMAIL')
    mail.Subject = "Candidates Comparison"
    mail.Body = str(response)
    mail.Send()
