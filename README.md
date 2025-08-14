# StatusSync - Job Application Email Parser

Automatically parse job application emails from Gmail using Google's Gemini AI to extract company names, position titles, and application statuses.

## Features

- **Gmail Integration**: Fetch emails from Gmail API between date ranges
- **AI-Powered Parsing**: Uses Google Gemini 2.5 Flash for accurate information extraction
- **HTML Email Cleaning**: Automatically strips HTML to provide clean text for analysis
- **Job Status Tracking**: Extracts company name, position title, and application status
- **Free Tier Compatible**: Uses Google's free Gemini API tier
- **External Prompt Templates**: Customizable AI prompts stored in text files

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials for a desktop application
5. Download credentials as `credentials.json` in the project root

### 3. Set Up Gemini API

1. Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set the environment variable:
   ```bash
   # Windows PowerShell
   $Env:GEMINI_API_KEY = "your-api-key-here"
   
   # Linux/Mac
   export GEMINI_API_KEY="your-api-key-here"
   ```

### 4. Run the Test

```bash
python simple_test.py
```

This will:
- Authenticate with Gmail
- Fetch emails from a specific date range
- Parse job application emails with AI
- Display extracted information
## Project Structure

```
StatusSync/
├── gmail_service.py          # Gmail API integration and HTML cleaning
├── job_application_parser.py # Gemini AI-powered email parsing
├── prompt_template.txt       # AI prompt template
├── simple_test.py           # Test script
├── requirements.txt         # Python dependencies
├── credentials.json         # Gmail OAuth credentials (you provide)
└── token.json              # Gmail auth token (auto-generated)
```

## Core Classes

### GmailService
- Handles Gmail API authentication
- Fetches emails between date ranges
- Strips HTML from email content using html2text

### JobApplicationParser
- Uses Google Gemini AI to extract job information
- Returns structured JobApplication objects
- Handles API errors and safety filter responses

### JobApplication
- Data class containing:
  - `company_name`: The hiring company
  - `position_title`: Job position title  
  - `status`: Application status (applied, rejected, interview_scheduled, etc.)
  - `confidence`: AI confidence level (0.0-1.0)

## Usage Example

```python
from gmail_service import GmailService
from job_application_parser import JobApplicationParser

# Initialize services
gmail = GmailService()
gmail.authenticate()
parser = JobApplicationParser()

# Get emails and parse
emails = gmail.get_emails("2023-09-26", "2023-09-27")
for email in emails:
    job_app = parser.parse_email(email)
    if job_app:
        print(f"{job_app.company_name}: {job_app.position_title} - {job_app.status}")
```

## Supported Application Statuses

- `applied` - Application submitted
- `rejected` - Application declined
- `interview_scheduled` - Interview arranged
- `interview_completed` - Interview finished
- `offer` - Job offer received
- `offer_accepted` - Offer accepted
- `offer_declined` - Offer declined
- `withdrawn` - Application withdrawn
- `on_hold` - Application paused
- `unknown` - Status unclear

## Customizing AI Prompts

Edit `prompt_template.txt` to customize how the AI analyzes emails. The template uses these variables:
- `{email_subject}` - Email subject line
- `{email_sender}` - Email sender address
- `{email_body}` - Email body content (first 1500 chars)

## API Limits

- **Gmail API**: 1 billion quota units per day (free)
- **Gemini API**: 15 requests per minute, 1 million tokens per day (free tier)
- The parser includes automatic rate limiting for free tier compliance

## Troubleshooting

**Gmail Authentication Issues:**
- Ensure `credentials.json` is in the project root
- Run the script and complete OAuth flow in browser

**Gemini API Errors:**
- Verify `GEMINI_API_KEY` environment variable is set
- Check API quota limits in Google AI Studio
- Content may be blocked by safety filters

**No Emails Found:**
- Verify date format (YYYY-MM-DD)
- Check Gmail account has emails in date range
- Try expanding date range

## License

MIT License - feel free to use and modify for your job search tracking needs!

All options stay within Google Cloud's free tier for typical usage.
