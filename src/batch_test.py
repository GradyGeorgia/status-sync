#!/usr/bin/env python3
from gmail_service import GmailService
from job_application_parser import JobApplicationParser

def main():
    # Initialize Gmail service and authenticate
    gmail = GmailService()
    gmail.authenticate()

    print("GETTING EMAILS")
    
    emails = gmail.get_emails(
        start_date="2023-9-1",
        end_date="2023-9-30"
    )

    print("RECIEVED EMAILS")

    if emails:
        sample_subjects = [email['subject'] for email in emails[:20]]

        print(f"\nEMAIL SUBJECTS:")
        for i, subject in enumerate(sample_subjects, 1):
            print(f"{i}. {subject[:60]}...")
        print("")

        parser = JobApplicationParser()
        batch_results = parser.classify_email_batch(sample_subjects)
        
        print(f"\nCLASSIFICATION RESULTS")
        job_related_emails = []
        
        for i, (subject, is_job_related) in enumerate(zip(sample_subjects, batch_results), 1):
            status = "JOB-RELATED" if is_job_related else "NOT JOB-RELATED"
            print(f"{i}. {status}: {subject[:60]}...")
            
            # Store job-related emails for extraction
            if is_job_related:
                job_related_emails.append((i-1, emails[i-1]))  # Store index and full email
        
        # Extract information from job-related emails
        if job_related_emails:
            print(f"\n{'='*70}")
            print(f"EXTRACTING INFORMATION FROM {len(job_related_emails)} JOB-RELATED EMAILS")
            print(f"{'='*70}")
            
            for idx, (email_idx, email) in enumerate(job_related_emails, 1):
                print(f"\n--- Email {idx}/{len(job_related_emails)} (Original #{email_idx + 1}) ---")
                print(f"Subject: {email['subject']}")
                print(f"From: {email['from']}")
                print(f"Extracting job application information...")
                
                # Extract job application data
                result = parser.extract_email_data(email)
                
                if result:
                    print(f"✓ Successfully extracted:")
                    print(f"  Is Job Application Update: {result.is_job_application_update}")
                    print(f"  Company: {result.company_name}")
                    print(f"  Position: {result.position_title}")
                    print(f"  Status: {result.status}")
                    print(f"  Confidence: {result.confidence}")
                else:
                    print("✗ Failed to extract job application information")
        else:
            print(f"\nNo job-related emails found in the sample.")

        
    
if __name__ == "__main__":
    main()