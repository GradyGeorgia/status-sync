import os
import base64
import re
import logging
from typing import List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import html2text

from models import Email

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailService:
    def __init__(self) -> None:
        self.service = None
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.credentials_file = os.path.join(parent_dir, 'credentials.json')
        self.token_file = os.path.join(parent_dir, 'token.json')
        
        self._html_converter = html2text.HTML2Text()
        self._html_converter.ignore_links = True
        self._html_converter.ignore_images = True
        self._html_converter.body_width = 0
        self._html_converter.unicode_snob = True
        
        self._authenticate()
    
    def _authenticate(self) -> bool:
        creds = None
        
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Gmail credentials file not found: {self.credentials_file}")
                    raise FileNotFoundError(f"Credentials file '{self.credentials_file}' not found!")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server()
            
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def get_emails(self, start_date: str, end_date: str, max_results: int = 100) -> List[Email]:
        if not self.service:
            raise RuntimeError("Gmail service not authenticated")
        
        query = f'after:{start_date} before:{end_date} category:primary'
        
        try:
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()
            
            messages = result.get('messages', [])
            
            if not messages:
                logger.warning(f"No emails found in date range {start_date} to {start_date}")
                return []
            
            parsed_emails = []
            for message in messages:
                try:
                    email_data = self._parse_single_email(message['id'])
                    parsed_emails.append(email_data)
                except Exception as e:
                    logger.warning(f"Failed to parse email: {e}")
                    continue
            
            return parsed_emails
            
        except Exception as error:
            logger.error(f"Gmail API error while retrieving emails: {error}")
            return []
        
    def _parse_single_email(self, message_id: str) -> Email:
        message = self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        headers = message['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        recipient = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        body = self._extract_body(message['payload'])
        
        return Email(
            subject=subject,
            body=body,
            sender=sender,
            recipient=recipient,
            date=date
        )
    
    def _extract_body(self, payload: dict) -> str:
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                body += self._extract_body(part)
        else:
            if payload.get('body') and payload['body'].get('data'):
                mime_type = payload.get('mimeType', '')
                if mime_type in ['text/plain', 'text/html']:
                    data = payload['body']['data']
                    decoded_data = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    
                    if mime_type == 'text/html':
                        decoded_data = self._strip_html(decoded_data)
                    
                    body += decoded_data
        
        return body

    def _strip_html(self, html_content: str) -> str:
        if not html_content:
            return ""
        clean_text = self._html_converter.handle(html_content)
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)
        return clean_text.strip()