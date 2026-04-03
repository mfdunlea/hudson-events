import os
import json
import base64
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = Credentials.from_authorized_user_info(
        json.loads(os.environ['GMAIL_TOKEN']), SCOPES
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('gmail', 'v1', credentials=creds)

def get_emails(service, max_results=50):
    results = service.users().messages().list(
        userId='me',
        maxResults=max_results,
        labelIds=['Label_6519375820666945615']
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for msg in messages:
        data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in data['payload']['headers']}
        subject = headers.get('Subject', '(no subject)')
        sender  = headers.get('From', '')
        date    = headers.get('Date', '')

        # Extract plain text body
        body = ""
        payload = data['payload']

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    raw = part['body'].get('data', '')
                    body = base64.urlsafe_b64decode(raw).decode('utf-8', errors='ignore')
                    break
        elif payload['body'].get('data'):
            raw = payload['body']['data']
            body = base64.urlsafe_b64decode(raw).decode('utf-8', errors='ignore')

        # Just take first 300 characters as preview
        preview = body.strip()[:300].replace('\n', ' ').replace('\r', '')

        emails.append({
            "sender":  sender,
            "subject": subject,
            "date":    date,
            "preview": preview
        })

    return emails

def main():
    service = get_gmail_service()
    emails  = get_emails(service)

    with open('business_updates.json', 'w') as f:
        json.dump(emails, f, indent=2)

    print(f"Done. {len(emails)} emails written to business_updates.json")

main()