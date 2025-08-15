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
        start_date="2023-11-9",
        end_date="2023-11-10"
    )

    print("RECIEVED EMAILS")
    
    # Find email from ge@myworkday.com for testing
    selected_email = None
    for email in emails:
        if 'workday@plexus.com' in email.get('from', ''):
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

    # Test batch classification
    print("\n" + "="*50)
    print("TESTING BATCH CLASSIFICATION")
    print("="*50)
    
    # Get a sample of email subjects for batch testing
    if emails:
        sample_subjects = [email['subject'] for email in emails[:5]]  # Test with first 5 emails
        
        print(f"Testing batch classification with {len(sample_subjects)} emails:")
        for i, subject in enumerate(sample_subjects, 1):
            print(f"{i}. {subject[:60]}...")
        
        # Test batch classification
        batch_results = parser.classify_email_batch(sample_subjects)
        
        print(f"\nBatch classification results:")
        for i, (subject, is_job_related) in enumerate(zip(sample_subjects, batch_results), 1):
            status = "JOB-RELATED" if is_job_related else "NOT JOB-RELATED"
            print(f"{i}. {status}: {subject[:60]}...")

if __name__ == "__main__":
    main()
