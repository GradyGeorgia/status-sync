#!/usr/bin/env python3
from gmail_service import GmailService
from job_application_parser import JobApplicationParser

def main():
    # Initialize Gmail service and authenticate
    gmail = GmailService()
    gmail.authenticate()

    print("GETTING EMAILS")
    
    # Get emails from September 26th, 2023
    emails = gmail.get_emails(
        start_date="2023-09-27",
        end_date="2023-09-28"
    )

    print("RECIEVED EMAILS")
    
    # Find email from ge@myworkday.com for testing
    selected_email = None
    for email in emails:
        if 'ge@myworkday.com' in email.get('from', ''):
            selected_email = email
            break
    
    if selected_email:

        print("EMAIL PREVIEW\n")

        print(f"Subject: {selected_email['subject']}")
        print(f"From: {selected_email['from']}")
        print(f"Body length: {len(selected_email['body'])} characters")
        print(f"Body preview (first 300 chars):\n{selected_email['body'][:300]}...\n")

        parser = JobApplicationParser()

        print("CLASSIFYING EMAIL")

        is_job_app_email = parser.classify_email(selected_email['subject'])
        
        print(f"CLASSIFIED AS JOB APP: {is_job_app_email}")

        if is_job_app_email:
            print("EXTRACTING INFO")

            result = parser.extract_email_data(selected_email)
            
            print(f"\nExtracted information:")
            if result:
                print(f"Company: {result.company_name}")
                print(f"Position: {result.position_title}")
                print(f"Status: {result.status}")
                print(f"Confidence: {result.confidence}\n")
            else:
                print("Failed to extract job application information\n")
    else:
        print("No email found from ge@myworkday.com")

if __name__ == "__main__":
    main()
