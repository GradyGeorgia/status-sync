import os
import logging
from typing import Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from models import JobApplicationStatus

logger = logging.getLogger(__name__)
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleSheetsService:
    def __init__(self) -> None:
        self.service = None
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.credentials_file = os.path.join(parent_dir, 'credentials.json')
        self.token_file = os.path.join(parent_dir, 'token_sheets.json')
        self.spreadsheet_id_file = os.path.join(parent_dir, 'spreadsheet_id.txt')
        
        self._authenticate()
        self._get_or_create_spreadsheet()
    
    def _authenticate(self) -> None:
        creds = None
        
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file '{self.credentials_file}' not found!")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('sheets', 'v4', credentials=creds)
        except HttpError as error:
            logger.error(f"Error occurred during Google Sheets authentication: {error}")
            raise

    def _get_or_create_spreadsheet(self) -> None:
        if os.path.exists(self.spreadsheet_id_file):
            try:
                with open(self.spreadsheet_id_file, 'r') as f:
                    spreadsheet_id = f.read().strip()
                    if spreadsheet_id:
                        self.spreadsheet_id = spreadsheet_id
                        return
            except IOError as e:
                logger.warning(f"Error reading spreadsheet ID file: {e}")
        
        self._create_sheet("Job Applications Tracker")
        
        try:
            with open(self.spreadsheet_id_file, 'w') as f:
                f.write(self.spreadsheet_id)
        except IOError as e:
            logger.warning(f"Error saving spreadsheet ID: {e}")
    
    def add_or_update_job_application(self, job_application: JobApplicationStatus, sheet_name: str = "Sheet1") -> None:
        unique_key = job_application.get_unique_key()
        existing_data = self._get_existing_data(sheet_name)
        
        if unique_key in existing_data:
            existing_status = existing_data[unique_key]['status']
            if existing_status != job_application.status:
                row_number = existing_data[unique_key]['row_number']
                self._update_row(row_number, job_application, existing_data[unique_key], sheet_name)
        else:
            self._add_row(job_application, sheet_name)

    def _create_sheet(self, title: str) -> None:
        if not self.service:
            raise ValueError("Service not authenticated. Call authenticate() first.")
        
        try:
            spreadsheet = {'properties': {'title': title}}
            sheet = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            self.spreadsheet_id = sheet.get('spreadsheetId')
            headers = ["Status", "Company", "Position", "Location", "Action Date"]
            self._add_headers(headers)
            
        except HttpError as error:
            logger.error(f"Error occurred while creating spreadsheet: {error}")
            raise

    def _add_headers(self, headers: list, sheet_name: str = "Sheet1") -> None:
        if not self.service:
            raise ValueError("Service not authenticated.")
        
        try:
            range_name = f"{sheet_name}!A1"
            value_range_body = {'values': [headers]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=value_range_body
            ).execute()
            
        except HttpError as error:
            logger.error(f"Error occurred while adding headers: {error}")
            raise

    def _get_existing_data(self, sheet_name: str = "Sheet1") -> Dict[str, Dict]:
        if not self.service:
            raise ValueError("Service not authenticated.")
        
        try:
            range_name = f"{sheet_name}!A:E"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            existing_data = {}
            
            for i, row in enumerate(values[1:], start=2):
                if len(row) >= 3:
                    status = row[0] if len(row) > 0 else ""
                    company = row[1] if len(row) > 1 else ""
                    position = row[2] if len(row) > 2 else ""
                    location = row[3] if len(row) > 3 else ""
                    action_date = row[4] if len(row) > 4 else ""
                    
                    unique_key = f"{company.strip().lower()}|{position.strip().lower()}"
                    existing_data[unique_key] = {
                        'row_number': i,
                        'status': status,
                        'company': company,
                        'position': position,
                        'location': location,
                        'action_date': action_date
                    }
            
            return existing_data
            
        except HttpError as error:
            logger.error(f"Error reading existing data: {error}")
            return {}
        
    def _add_row(self, job_application: JobApplicationStatus, sheet_name: str = "Sheet1") -> None:
        if not self.service:
            raise ValueError("Service not authenticated.")
        
        try:
            data_row = [
                job_application.status,
                job_application.company_name,
                job_application.position_title,
                job_application.position_location,
                job_application.action_date
            ]
            
            range_name = f"{sheet_name}!A:E"
            value_range_body = {'values': [data_row]}
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=value_range_body
            ).execute()
            
        except HttpError as error:
            logger.error(f"Error occurred while adding data row: {error}")
            raise

    def _update_row(self, row_number: int, job_application: JobApplicationStatus, existing_row_data: Dict, sheet_name: str = "Sheet1") -> None:
        if not self.service:
            raise ValueError("Service not authenticated.")
        
        try:
            data_row = [
                job_application.status if job_application.status != "unknown" else existing_row_data.get('status', ''),
                job_application.company_name if job_application.company_name != "unknown" else existing_row_data.get('company', ''),
                job_application.position_title if job_application.position_title != "unknown" else existing_row_data.get('position', ''),
                job_application.position_location if job_application.position_location != "unknown" else existing_row_data.get('location', ''),
                job_application.action_date if job_application.action_date != "unknown" else existing_row_data.get('action_date', '')
            ]
            
            range_name = f"{sheet_name}!A{row_number}:E{row_number}"
            value_range_body = {'values': [data_row]}
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=value_range_body
            ).execute()
            
        except HttpError as error:
            logger.error(f"Error updating row {row_number}: {error}")
            raise