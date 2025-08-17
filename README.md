# StatusSync - Job Application Email Parser & Tracker

Automatically parse job application emails from Gmail using Google's Gemini AI and track them in Google Sheets. Extract company names, position titles, application statuses, and sync everything to a spreadsheet for easy tracking.

## Features

- **Gmail Integration**: Fetch emails from Gmail API between date ranges
- **AI-Powered Parsing**: Uses Google Gemini 2.5 Flash for accurate information extraction
- **Email Classification**: Batch classify emails to identify job-related messages
- **HTML Email Cleaning**: Automatically strips HTML to provide clean text for analysis
- **Job Status Tracking**: Extracts company name, position title, and application status
- **Google Sheets Integration**: Automatically creates and updates a tracking spreadsheet
- **Batch Processing**: Efficient batch processing for multiple emails
- **Free Tier Compatible**: Uses Google's free Gemini API tier
- **External Prompt Templates**: Customizable AI prompts stored in text files
- **Persistent Storage**: Reuses the same spreadsheet across program runs

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

### 3. Set Up Google Sheets API

1. In the same Google Cloud Console project
2. Enable Google Sheets API
3. Use the same `credentials.json` file

### 4. Set Up Gemini API

1. Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set the environment variable:
   ```bash
   # Windows PowerShell
   $Env:GEMINI_API_KEY = "your-api-key-here"
   
   # Linux/Mac
   export GEMINI_API_KEY="your-api-key-here"
   ```

### 5. Run the Main Program

```bash
python main.py
```

This will:
- Authenticate with Gmail and Google Sheets
- Fetch and classify emails from your specified date range
- Extract job application information using AI
- Create/update a Google Sheets tracker with your job applications
## Project Structure

```
StatusSync/
├── src/                              # Source code
│   ├── gmail_service.py             # Gmail API integration and HTML cleaning
│   ├── job_application_parser.py    # Gemini AI-powered email parsing and classification
│   ├── google_spreadsheet_service.py # Google Sheets integration
│   ├── main.py                      # Main application runner
│   ├── simple_test.py               # Basic test script
│   ├── batch_test.py                # Batch processing test
│   └── example_job_app_info.py      # Example job application data
├── prompt_templates/                 # AI prompt templates
│   ├── classification_template.txt  # Email classification prompt
│   ├── extraction_template.txt      # Job data extraction prompt
│   └── batch_classification_template.txt # Batch classification prompt
├── requirements.txt                 # Python dependencies
├── credentials.json                 # Gmail/Sheets OAuth credentials (you provide)
├── token.json                      # Gmail auth token (auto-generated)
├── token_sheets.json               # Google Sheets auth token (auto-generated)
└── spreadsheet_id.txt              # Stores spreadsheet ID for reuse (auto-generated)
```

## Core Classes

### GmailService
- Handles Gmail API authentication
- Fetches emails between date ranges
- Strips HTML from email content using html2text

### JobApplicationParser
- Uses Google Gemini AI to extract job information
- Batch classification of emails to filter job-related messages
- Returns structured JobApplication objects
- Handles API errors and safety filter responses

### GoogleSheetsService
- Handles Google Sheets API authentication
- Creates and manages job application tracking spreadsheet
- Automatically reuses the same spreadsheet across runs
- Adds job application data as rows

### JobApplication
- Data class containing:
  - `company_name`: The hiring company
  - `position_title`: Job position title  
  - `status`: Application status (applied, rejected, interview_scheduled, etc.)
  - `is_job_application_update`: Boolean indicating if this is an actual job update
  - `confidence`: AI confidence level (0.0-1.0)

## Usage Example

```python
from src.gmail_service import GmailService
from src.job_application_parser import JobApplicationParser
from src.google_spreadsheet_service import GoogleSheetsService

# Initialize services
gmail = GmailService()
parser = JobApplicationParser()
sheets = GoogleSheetsService()  # Automatically creates/reuses spreadsheet

# Get and filter emails
emails = gmail.get_emails("2023-09-01", "2023-09-30")
job_emails = parser.filter_emails(emails)  # Batch classification

# Extract job application data and add to spreadsheet
for email in job_emails:
    job_app = parser.extract_email_data(email)
    if job_app and job_app.is_job_application_update:
        sheets.add_data_row(job_app)
        print(f"Added: {job_app.company_name} - {job_app.position_title}")
```

## Test Scripts

- **`main.py`**: Full pipeline from Gmail to Google Sheets
- **`simple_test.py`**: Basic email fetching and parsing test
- **`batch_test.py`**: Demonstrates batch email classification and extraction

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

## AI Features

### Email Classification
The system uses batch processing to efficiently classify multiple emails at once, identifying which emails are related to job applications vs. promotional content or unrelated messages.

### Job Application Updates
The AI distinguishes between:
- **Actual job application updates** (status changes, interview invitations, etc.)
- **Job advertisements** (promotional emails about open positions)

### Customizing AI Prompts

Edit the template files in the `prompt_templates/` directory to customize how the AI analyzes emails:
- `classification_template.txt` - Controls email classification logic
- `batch_classification_template.txt` - Controls batch email classification
- `extraction_template.txt` - Controls job application data extraction

The extraction template uses these variables:
- `{email_subject}` - Email subject line
- `{email_sender}` - Email sender address
- `{email_body}` - Email body content (first 1500 chars)

## Google Sheets Integration

The system automatically:
1. **Creates a spreadsheet** on first run titled "Job Applications Tracker"
2. **Reuses the same spreadsheet** on subsequent runs (ID stored in `spreadsheet_id.txt`)
3. **Adds headers** with columns for Status, Company, and Position
4. **Appends job application data** as new rows
5. **Uses minimal permissions** - only accesses files the app creates

The spreadsheet URL is printed to the console for easy access.