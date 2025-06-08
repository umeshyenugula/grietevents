import os
import base64
import pickle
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
def gmail_authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)
def render_template(template_file, context):
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(template_file)
    return template.render(context)
def send_html_email(receiver,name,date,rollno,branch,eventname,verifynum):
    html_content = render_template('emailhtml.html', {
    'name': name,
    'Event_Date': date,
    'branch': branch,
    'roll':rollno,
    'eventname':eventname,
    'verify':verifynum
    })
    service = gmail_authenticate()
    message = MIMEText(html_content, 'html')
    message['to'] = receiver
    message['from'] = "me"
    message['subject'] = "Event Registration Succesful"
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw_message}
    try:
        sent = service.users().messages().send(userId="me", body=body).execute()
        return sent['id']
    except Exception as e:
        return e
