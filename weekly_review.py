import win32com.client, datetime
from datetime import date
from dateutil.parser import parse
import re
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

#Access Outlook
Outlook = win32com.client.Dispatch('Outlook.Application')
ns = Outlook.GetNamespace('MAPI')

#Remove specail character, url, and Team online meeting info
def clean_body(body):
    # Remove URLs
    body = re.sub(r'http\S+|www\S+|https\S+', '', body, flags=re.MULTILINE)    
    # Remove backslashes and the first letter after each backslash
    body = re.sub(r'\\.', '', body)
    # Remove special characters
    body = re.sub(r'[^A-Za-z0-9\s]+', ' ', body)    
    # Remove everything after "Microsoft Teams meeting"
    body = re.split(r'Microsoft Teams', body, flags=re.IGNORECASE)[0]
    # Remove single letters (except 'I' and 'a')
    body = re.sub(r'\b(?!I\b|a\b)[A-Za-z]\b', '', body)
    # Remove extra whitespace
    body = ' '.join(body.split())
    return body.strip()

#Get Calendar information
calendar = ns.GetDefaultFolder(9).Items
calendar.Sort('[Start]')
calendar.IncludeRecurrences = 'True'

#Set date range for calendar events
end = date.today() + datetime.timedelta(days=7)
end = end.strftime('%m/%d/%Y')
begin = date.today() - datetime.timedelta(days=7)
begin = begin.strftime('%m/%d/%Y')
calendar = calendar.Restrict("[Start] >= '" +begin+ "' AND [END] <= '" +end+ "'")

calendarDict = {}
item = 0

for indx, a in enumerate(calendar):
    subject = str(a.Subject)
    organizer = str(a.Organizer)
    meetingDate = str(a.Start)
    start_datetime = parse(meetingDate)
    date = start_datetime.date()
    time = start_datetime.time()
    duration = str(a.duration)
    body = str(a.Body.encode("utf8"))
    body = clean_body(body)
    participants = []
    for r in a.Recipients:
        participants.append(str(r))
    
    calendarDict[item] = {
        'Duration': duration, 
        'Organizer': organizer, 
        'Subject': subject, 
        'Date': date.strftime('%m/%d/%Y'),
        'Time': time.strftime('%H:%M:%S'),
        'Agenda': body,
        'Participants': ', '.join(participants)
    }
    item = item + 1

#Convert to string for Gemini
calendar_str = json.dumps(calendarDict)


#Clean up email body
def clean_body(email_body):
    # Remove URLs
    email_body = re.sub(r'http\S+', '', email_body)
    email_body = re.sub(r'www.\S+', '', email_body)
    
    # Remove email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    email_body = re.sub(email_pattern, '', email_body)
    
    # Remove unwanted characters
    email_body = re.sub(r'[<>]', '', email_body)
    email_body = email_body.replace('mailto:', '')
    email_body = re.sub(r'\\x[0-9a-fA-F]{2}', '',email_body)
    email_body = re.sub(r'_+', '',email_body)

    # Remove everything after "This RPT has been auto-generated"
    email_body = re.split(r'This RPT has been auto-generated', email_body, flags=re.IGNORECASE)[0]
    
    # Remove addresses (basic patterns for US addresses)
    email_body = re.sub(r'\b\d{1,5}\s[A-Za-z0-9\s,\.]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Parkway|Pkwy|Place|Pl|Fwy)\b', '', email_body, flags=re.IGNORECASE)
    email_body = re.sub(r'\b(?:[A-Za-z]+\s){1,3}\d{5}(?:-\d{4})?\b', '', email_body)  # City, State ZIP pattern

    # Remove signatures and other unnecessary lines
    signature_keywords = ["Cheers", "Best regards", "Thank you", "Regards", "Sent from my", "CROWN CASTLE", "CROWNCASTLE.COM","CrownCastle.com","M:","T:","O:","MObile:",]
     
    # Join the clean lines back into a single string
    body_lines = email_body.split('\\r\\n')
    clean_lines = []
    for line in body_lines:
        if not any(keyword in line for keyword in signature_keywords):
            clean_lines.append(line)
    
    # Further clean up for any excessive whitespace
    clean_body = ' '.join(clean_lines)      
    clean_body = re.sub(r'\s+', ' ', clean_body).strip()
    email_body = re.sub(r'\\.', '', clean_body)
    
    return email_body

#Get email from inbox. For other folders using current = inbox.Folders['Current']
inbox = ns.GetDefaultFolder(6)
messages = inbox.Items
messages.Sort("[ReceivedTime]", True)

msgDict = {}
item = 0

for msg in messages:
    subject = str(msg.Subject)
    to = str(msg.To)
    sender = str(msg.Sender)
    date = msg.SentOn.date()
    time = msg.SentOn.time()
    body = str(msg.Body.encode("utf8"))
    body = clean_body(body)
    if date>date.today()- datetime.timedelta(days=7):
        category = 'Aging: Within 7 days'
    else: 
        category = 'Aging: More than 7 days old'
    
    msgDict[item] = {
        'Subject': subject, 
        'Recipients': to,
        'Sender': sender,
        'Date': date.strftime('%m/%d/%Y'),
        'Time': time.strftime('%H:%M:%S'),
        'Message': body,
        'Aging Category': category
    }
    item = item + 1

#Convert to string for Gemini
email_str = json.dumps(msgDict)

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
      "parts": [email_str, calendar_str]
    }
  ]
)

chat_session.send_message('These are emails I received and calendar for this week and next week. Please summarize these information into three category: things I accomplished, on going, and next step.')

# Get the response
response = chat_session.last.text

# Present the response and ask for feedback
print(response)

#email myself the result
mail = Outlook.CreateItem(0)
mail.To = os.getenv('MY_EMAIL')
mail.Subject = 'Email Summary'
mail.Body = response
mail.Send()

