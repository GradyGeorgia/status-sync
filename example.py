from gmail_parser import GmailParser
from datetime import datetime, timedelta

def example_usage():
    """Example showing different ways to use the Gmail parser"""
    
    # Initialize the parser
    parser = GmailParser()
    
    # Authenticate with Gmail
    parser.authenticate()
    
    # Example 1: Get emails from specific date range
    print("=== Example 1: Specific Date Range ===")
    emails = parser.get_emails_between_dates(
        start_date="2024-01-01",
        end_date="2024-01-31",
        max_results=20
    )
    
    if emails:
        print(f"Found {len(emails)} emails in January 2024")
        for email in emails[:3]:  # Show first 3
            print(f"- {email['subject']} from {email['from']}")
    
    # Example 2: Get emails from last week
    print("\n=== Example 2: Last 7 Days ===")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    emails = parser.get_emails_between_dates(
        start_date=start_date,
        end_date=end_date,
        max_results=30
    )
    
    if emails:
        print(f"Found {len(emails)} emails in the last 7 days")
        
        # Filter by sender
        important_senders = ['noreply@github.com', 'support@']
        filtered_emails = [
            email for email in emails 
            if any(sender in email['from'].lower() for sender in important_senders)
        ]
        
        print(f"Filtered to {len(filtered_emails)} emails from important senders")
    
    # Example 3: Search with custom criteria
    print("\n=== Example 3: Custom Search ===")
    # You can modify the query in the class to add more filters
    # For example, search for emails with specific subject or from specific sender
    
    return emails

if __name__ == "__main__":
    example_usage()
