import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from job_application_parser import JobApplication
from example_job_app_info import email_data_list

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
            print(f"An error occurred during authentication: {error}")
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
                print(f"Error reading spreadsheet ID file: {e}")
        
        # Create new spreadsheet if no existing ID found
        spreadsheet_id = self.create_sheet("Job Applications Tracker")
        
        # Save the spreadsheet ID to file
        try:
            with open(self.spreadsheet_id_file, 'w') as f:
                f.write(spreadsheet_id)
        except IOError as e:
            print(f"Error saving spreadsheet ID: {e}")
        
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
            sheets_service.add_headers(headers)
            
            return spreadsheet_id
            
        except HttpError as error:
            print(f"An error occurred while creating spreadsheet: {error}")
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
            print(f"An error occurred while adding headers: {error}")
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
            print(f"An error occurred while adding data row: {error}")
            raise