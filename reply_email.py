import win32com.client, datetime
from datetime import date
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

#setup access to email folder
outlook = win32com.client.Dispatch('Outlook.Application')
ns = outlook.GetNamespace('MAPI')
inbox = ns.GetDefaultFolder(6)
messages = inbox.Items

#Search email with specific subject
search = str(input('Enter Subject'))
msgDict = {}
item = 0                
for msg in messages:
    if msg.Subject == search:
        subject = str(msg.Subject)
        to = str(msg.To)
        sender = str(msg.Sender)
        date = msg.SentOn.date()
        time = msg.SentOn.time()
        body = str(msg.Body.encode("utf8"))
        #body = clean_body(body)  
        msgDict[item] = {
            'Subject': subject, 
            'Recipients': to,
            'Sender': sender,
            'Date': date.strftime('%m/%d/%Y'),
            'Time': time.strftime('%H:%M:%S'),
            'Message': body
    }
    item = item + 1       
#Convert to string for Gemini
email = json.dumps(msgDict)

#Load API key
load_dotenv()
GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": email,
    }
  ]
)

chat_session.send_message('This is an email that I received. Subject, Date, Time, and Message are provided. I am manager of business performance analytics and you are my assistant. Please write a summary of the email I received and a professional response to the sender.')

# Get the response
response = chat_session.last.text

# Present the response and ask for feedback
print(response)
