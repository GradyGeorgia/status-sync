#!/usr/bin/env python3
from gmail_service import GmailService
from google_spreadsheet_service import GoogleSheetsService
from job_application_parser import JobApplicationParser

MAX_EMAILS_TO_PROCESS = 20
START_DATE = "2023-9-1"
END_DATE = "2023-9-30"

def main():
    print("SETTING UP GMAIL SERVICE")
    gmail_service = GmailService()

    print("RETRIEVING EMAILS")
    emails = gmail_service.get_emails(
        start_date = START_DATE,
        end_date = END_DATE
    )
    if not emails:
        return
    emails = [email for email in emails if email["subject"]][:MAX_EMAILS_TO_PROCESS]
    print(f"PROCESSING {len(emails)} EMAILS")

    print("SETTING UP JOB APPLICATION PARSER")
    job_application_parser = JobApplicationParser()
    
    print(f"CLASSIFYING {len(emails)} EMAILS")
    job_app_emails = job_application_parser.filter_emails(emails)
    print(f"FOUND {len(job_app_emails)} JOB APP EMAILS")

    print("EXTRACTING INFO FROM EMAILS")
    job_app_data = [job_application_parser.extract_email_data(email) for email in job_app_emails]
    print("EXTRACTED INFO FROM EMAILS")

    print("SETTING UP GOOGLE SPREADSHEET SERVICE")
    google_sheets_service = GoogleSheetsService()

    print("UPDATING SPREADSHEET")
    for job_app in job_app_data:
        google_sheets_service.add_data_row(job_app)

    print("COMPLETED")

if __name__ == "__main__":
    main()