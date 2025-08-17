import os
import base64
import re
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import html2text

# Gmail API scope for reading emails
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Initialize html2text converter
h = html2text.HTML2Text()
h.ignore_links = True
h.ignore_images = True
h.body_width = 0  # Don't wrap lines
h.unicode_snob = True  # Better Unicode handling

def strip_html(html_content: str) -> str:
    """Strip HTML tags and clean up text content using html2text"""
    if not html_content:
        return ""
    
    # Use html2text to convert HTML to clean text
    clean_text = h.handle(html_content)
    
    # Clean up extra whitespace
    clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)  # Multiple newlines to double newlines
    clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # Multiple spaces/tabs to single space
    clean_text = clean_text.strip()
    
    return clean_text

class GmailService:
    def __init__(self):
        """Initialize the Gmail service"""
        self.service = None
        # Look for credentials in the parent directory (project root)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.credentials_file = os.path.join(parent_dir, 'credentials.json')
        self.token_file = os.path.join(parent_dir, 'token.json')

        self.authenticate()
    
    def authenticate(self):
        """Gmail API authentication"""
        creds = None

        # Use saved credentials
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # Log in if no valid saved credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file '{self.credentials_file}' not found!")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                creds = flow.run_local_server()

            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        return True
    
    def _parse_date(self, date_string):
        """Parse date string or datetime object to Gmail API format"""
        if isinstance(date_string, str):
            try:
                dt = datetime.strptime(date_string, '%Y-%m-%d')
            except ValueError:
                try:
                    dt = datetime.strptime(date_string, '%Y/%m/%d')
                except ValueError:
                    raise ValueError(f"Invalid date format: {date_string}. Use YYYY-MM-DD or YYYY/MM/DD")
        elif isinstance(date_string, datetime):
            dt = date_string
        else:
            raise ValueError("Date must be string or datetime object")
        
        return dt.strftime('%Y/%m/%d')
    
    def _extract_body(self, payload):
        """Extract email body from payload and strip HTML"""
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
                        decoded_data = strip_html(decoded_data)
                    
                    body += decoded_data
        
        return body
    
    def get_emails(self, start_date, end_date, max_results=100):
        """
        Get emails between two dates
        
        Args:
            start_date: Start date (string YYYY-MM-DD or datetime object)
            end_date: End date (string YYYY-MM-DD or datetime object)
            max_results: Maximum number of emails to retrieve (default: 100)
        
        Returns:
            List of dictionaries with 'subject', 'body', 'date', 'from', 'to'
        """
        if not self.service:
            raise RuntimeError("Not authenticated")
        
        start_str = self._parse_date(start_date)
        end_str = self._parse_date(end_date)
        
        query = f'after:{start_str} before:{end_str} category:primary'
        
        try:
            # Get message list
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()
            
            messages = result.get('messages', [])
            
            if not messages:
                print("No emails found in the specified date range")
                return []
            
            # Parse each email
            parsed_emails = []
            for i, msg in enumerate(messages, 1):
                try:
                    email_data = self._parse_single_email(msg['id'])
                    parsed_emails.append(email_data)
                except Exception as e:
                    print(f"Error parsing email {i}: {e}")
                    continue
            
            return parsed_emails
            
        except Exception as error:
            print(f"An error occurred: {error}")
            return []
    
    def _parse_single_email(self, message_id):
        """Parse a single email by message ID"""
        # Get the message
        message = self.service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = message['payload'].get('headers', [])
        
        # Extract specific header values
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        recipient = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        
        # Extract body
        body = self._extract_body(message['payload'])
        
        return {
            'subject': subject,
            'body': body,
            'date': date,
            'from': sender,
            'to': recipient
        }