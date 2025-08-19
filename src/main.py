#!/usr/bin/env python3
import logging
from gmail_service import GmailService
from google_sheets_service import GoogleSheetsService
from job_application_parser import JobApplicationParser

MAX_EMAILS_TO_PROCESS = 20
START_DATE = "2023/9/1"
END_DATE = "2023/9/30"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('statussync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Setting up Gmail service")
    gmail_service = GmailService()

    logger.info(f"Retrieving emails from {START_DATE} to {END_DATE}")
    emails = gmail_service.get_emails(
        start_date = START_DATE,
        end_date = END_DATE
    )
    logger.info(f"Retrieved {len(emails)} emails")
    emails = [email for email in emails if email.subject.strip()][:MAX_EMAILS_TO_PROCESS]
    if not emails:
        logger.info("No emails found to process")
        return
    logger.info(f"Processing {len(emails)} emails")

    logger.info("Setting up job application parser")
    job_application_parser = JobApplicationParser()
    
    logger.info(f"Classifying {len(emails)} emails")
    job_app_emails = job_application_parser.filter_emails(emails)
    if not job_app_emails:
        logger.info("No job application emails found")
        return
    logger.info(f"Found {len(job_app_emails)} job application emails")

    logger.info("Extracting information from job application emails")
    job_app_statuses = [job_application_parser.extract_email_data(email) for email in job_app_emails]
    job_app_statuses = [job_app_status for job_app_status in job_app_statuses if job_app_status is not None]
    job_app_statuses = [job_app_status for job_app_status in job_app_statuses if job_app_status.is_job_application_update]
    if not job_app_statuses:
        logger.info("No valid job application data extracted")
        return
    logger.info(f"Successfully extracted information from {len(job_app_statuses)} emails")

    logger.info("Setting up Google Spreadsheet service")
    google_sheets_service = GoogleSheetsService()

    logger.info("Updating spreadsheet with job application data")    
    for job_app_status in job_app_statuses:
        google_sheets_service.add_or_update_job_application(job_app_status)
    logger.info(f"Spreadsheet update completed")

if __name__ == "__main__":
    try:
        main()
        logger.info("Program completed successfully")
    except Exception as e:
        logger.error(f"Program failed with error: {e}")
        raise