#!/usr/bin/env python3
from src.gmail_service import GmailService
from src.job_application_parser import JobApplicationParser

def main():
    # Initialize Gmail service and authenticate
    gmail = GmailService()
    gmail.authenticate()
    
    # Get emails from September 26th, 2023
    emails = gmail.get_emails(
        start_date="2023-09-26",
        end_date="2023-09-28"
    )
    
    # Find email from ge@myworkday.com for testing
    workday_email = None
    for email in emails:
        if 'ge@myworkday.com' in email.get('from', ''):
            workday_email = email
            break
    
    if workday_email:
        print(f"\nEmail from ge@myworkday.com:")
        print(f"Subject: {workday_email['subject']}")
        print(f"From: {workday_email['from']}")
        print(f"Body length: {len(workday_email['body'])} characters")
        print(f"Body preview (first 300 chars):\n{workday_email['body'][:300]}...")
        
        # Parse with job application parser
        print(f"\nAttempting to parse email with Gemini AI...")
        parser = JobApplicationParser()
        result = parser.extract_email_data(workday_email)
        
        print(f"\nExtracted information:")
        if result:
            print(f"Company: {result.company_name}")
            print(f"Position: {result.position_title}")
            print(f"Status: {result.status}")
            print(f"Confidence: {result.confidence}")
        else:
            print("Failed to extract job application information")
    else:
        print("No email found from ge@myworkday.com")

if __name__ == "__main__":
    main()
