import os
import logging
from typing import Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from models import JobApplication

# Setup logging for this module
logger = logging.getLogger(__name__)

# Google Sheets API scope - create and manage spreadsheets only (no access to existing sheets)
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleSheetsService:
    def __init__(self):
        """Initialize the Google Sheets service and get/create spreadsheet"""
        self.service = None
        # Look for credentials in the parent directory (project root)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.credentials_file = os.path.join(parent_dir, 'credentials.json')
        self.token_file = os.path.join(parent_dir, 'token_sheets.json')
        self.spreadsheet_id_file = os.path.join(parent_dir, 'spreadsheet_id.txt')
        
        # Authenticate and get/create spreadsheet
        self.authenticate()
        self.spreadsheet_id = self._get_or_create_spreadsheet()
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
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
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())

        try:
            self.service = build('sheets', 'v4', credentials=creds)
        except HttpError as error:
            logger.error(f"Error occurred during Google Sheets authentication: {error}")
            raise

    def _get_or_create_spreadsheet(self) -> str:
        """
        Get existing spreadsheet ID from file or create a new spreadsheet
        
        Returns:
            str: The spreadsheet ID
        """
        # Check if spreadsheet ID file exists
        if os.path.exists(self.spreadsheet_id_file):
            try:
                with open(self.spreadsheet_id_file, 'r') as f:
                    spreadsheet_id = f.read().strip()
                    if spreadsheet_id:
                        return spreadsheet_id
            except IOError as e:
                logger.warning(f"Error reading spreadsheet ID file: {e}")
        
        # Create new spreadsheet if no existing ID found
        spreadsheet_id = self.create_sheet("Job Applications Tracker")
        
        # Save the spreadsheet ID to file
        try:
            with open(self.spreadsheet_id_file, 'w') as f:
                f.write(spreadsheet_id)
        except IOError as e:
            logger.warning(f"Error saving spreadsheet ID: {e}")
        
        return spreadsheet_id

    def create_sheet(self, title: str) -> str:
        """
        Create a new Google Spreadsheet
        
        Args:
            title: The title for the new spreadsheet
            
        Returns:
            str: The spreadsheet ID of the created sheet
        """
        if not self.service:
            raise ValueError("Service not authenticated. Call authenticate() first.")
        
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            sheet = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            spreadsheet_id = sheet.get('spreadsheetId')

            headers = ["Status", "Company", "Position"]
            self.add_headers(headers)
            
            return spreadsheet_id
            
        except HttpError as error:
            logger.error(f"Error occurred while creating spreadsheet: {error}")
            raise

    def add_headers(self, headers: list, sheet_name: str = "Sheet1"):
        """
        Add headers to the first row of the spreadsheet
        
        Args:
            headers: List of header strings
            sheet_name: Name of the sheet to add headers to (default: "Sheet1")
        """
        if not self.service:
            raise ValueError("Service not authenticated.")
        
        try:
            range_name = f"{sheet_name}!A1"
            value_range_body = {
                'values': [headers]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=value_range_body
            ).execute()
            
        except HttpError as error:
            logger.error(f"Error occurred while adding headers: {error}")
            raise

    def add_data_row(self, job_application: JobApplication, sheet_name: str = "Sheet1"):
        """
        Add a job application data row to the spreadsheet
        
        Args:
            job_application: JobApplication object containing the data
            sheet_name: Name of the sheet to add data to (default: "Sheet1")
        """
        if not self.service:
            raise ValueError("Service not authenticated.")
        
        try:
            # Prepare the data row with status, company, and position
            data_row = [
                job_application.status,
                job_application.company_name,
                job_application.position_title
            ]
            
            # Append the row to the sheet
            range_name = f"{sheet_name}!A:C"
            value_range_body = {
                'values': [data_row]
            }
            
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

    def get_existing_data(self, sheet_name: str = "Sheet1") -> Dict[str, Dict]:
        """
        Get all existing data from the spreadsheet
        
        Returns:
            Dict mapping unique keys to row data (including row number)
        """
        if not self.service:
            raise ValueError("Service not authenticated.")
        
        try:
            # Get all data from the sheet
            range_name = f"{sheet_name}!A:C"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            existing_data = {}
            
            # Skip header row (index 0), start from row 1
            for i, row in enumerate(values[1:], start=2):  # start=2 because spreadsheet rows are 1-indexed
                if len(row) >= 3:  # Ensure we have status, company, position
                    status, company, position = row[0], row[1], row[2]
                    unique_key = f"{company.strip().lower()}|{position.strip().lower()}"
                    existing_data[unique_key] = {
                        'row_number': i,
                        'status': status,
                        'company': company,
                        'position': position
                    }
            
            return existing_data
            
        except HttpError as error:
            logger.error(f"Error reading existing data: {error}")
            return {}

    def update_row(self, row_number: int, job_application: JobApplication, sheet_name: str = "Sheet1"):
        """
        Update a specific row with new job application data
        
        Args:
            row_number: The row number to update (1-indexed)
            job_application: JobApplication object with updated data
            sheet_name: Name of the sheet
        """
        if not self.service:
            raise ValueError("Service not authenticated.")
        
        try:
            range_name = f"{sheet_name}!A{row_number}:C{row_number}"
            data_row = [
                job_application.status,
                job_application.company_name,
                job_application.position_title
            ]
            
            value_range_body = {
                'values': [data_row]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=value_range_body
            ).execute()
            
        except HttpError as error:
            logger.error(f"Error updating row {row_number}: {error}")
            raise

    def add_or_update_job_application(self, job_application: JobApplication, sheet_name: str = "Sheet1"):
        """
        Add new job application or update existing one based on company + position
        
        Args:
            job_application: JobApplication object
            sheet_name: Name of the sheet
        """
        # Get unique key for this job application
        unique_key = job_application.get_unique_key()
        
        # Get existing data
        existing_data = self.get_existing_data(sheet_name)
        
        if unique_key in existing_data:
            # Check if status has changed
            existing_status = existing_data[unique_key]['status']
            if existing_status != job_application.status:
                # Update existing row
                row_number = existing_data[unique_key]['row_number']
                self.update_row(row_number, job_application, sheet_name)
                return 'updated'
            else:
                return 'no_change'
        else:
            # Add new row
            self.add_data_row(job_application, sheet_name)
            return 'added'