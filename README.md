# Gmail Email Parser

This project provides a Python script to parse emails from Gmail between two specified dates using the Gmail API.

## Features

- Authenticate with Gmail API using OAuth 2.0
- Fetch emails between specific date ranges
- Parse email content including headers, body, and metadata
- Save parsed emails to file
- Support for various date formats
- Error handling and logging

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Gmail API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client ID"
   - Choose "Desktop application"
   - Download the JSON file and save it as `credentials.json` in this directory

### 3. First Run

On the first run, the script will open a browser window for authentication. After successful authentication, a `token.pickle` file will be created for subsequent runs.

## Usage

### Basic Usage

```python
from gmail_parser import GmailParser
from datetime import datetime, timedelta

# Initialize parser
parser = GmailParser()

# Authenticate
parser.authenticate()

# Get emails from last 7 days
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

emails = parser.get_emails_between_dates(
    start_date=start_date,
    end_date=end_date,
    max_results=50
)

# Save to file
parser.save_emails_to_file(emails, 'my_emails.txt')
```

### Using Specific Dates

```python
# Using string dates
emails = parser.get_emails_between_dates(
    start_date="2024-01-01",
    end_date="2024-01-31",
    max_results=100
)

# Using datetime objects
from datetime import datetime
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 31)

emails = parser.get_emails_between_dates(
    start_date=start,
    end_date=end,
    max_results=100
)
```

## Running the Examples

```bash
# Run the main example
python gmail_parser.py

# Run additional examples
python example.py
```

## Email Data Structure

Each parsed email contains the following information:

```python
{
    'id': 'message_id',
    'thread_id': 'thread_id',
    'subject': 'Email Subject',
    'from': 'sender@example.com',
    'to': 'recipient@example.com',
    'date': 'Original date string',
    'parsed_date': datetime_object,
    'cc': 'cc@example.com',
    'bcc': 'bcc@example.com',
    'labels': ['INBOX', 'IMPORTANT'],
    'snippet': 'Email preview text...',
    'body': 'Full email body content'
}
```

## Error Handling

The script includes comprehensive error handling for:
- Authentication failures
- Invalid date formats
- Network issues
- Malformed emails
- API quota limits

## Security Notes

- The `credentials.json` file contains sensitive information - do not commit it to version control
- The `token.pickle` file contains your access token - keep it secure
- Add both files to your `.gitignore`

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**: Make sure you've downloaded and placed the `credentials.json` file in the project directory
2. **"Authentication failed"**: Delete the `token.pickle` file and re-authenticate
3. **"No emails found"**: Check your date range and ensure there are emails in that period
4. **"API quota exceeded"**: The Gmail API has usage limits - wait before making more requests

### Date Format Examples

The parser supports various date formats:
- "2024-01-01"
- "January 1, 2024"
- "01/01/2024"
- "2024-01-01 10:30:00"
- datetime objects

## Customization

You can extend the `GmailParser` class to add more features:
- Filter by sender, subject, or labels
- Extract attachments
- Parse HTML content
- Export to different formats (CSV, JSON)
- Add custom search queries
