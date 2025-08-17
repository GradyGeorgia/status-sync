import os
import json
import re
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple
import google.generativeai as genai

@dataclass
class JobApplication:
    company_name: str
    position_title: str
    status: str
    is_job_application_update: bool = False
    confidence: float = 0.0

class JobApplicationParser:
    def __init__(self):
        """Initialize with Gemini AI"""
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.status_categories = [
            "applied", "rejected", "interview_scheduled", "interview_completed", 
            "offer", "offer_accepted", "offer_declined", "withdrawn", "on_hold", "unknown"
        ]
    
    def _send_to_gemini(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        Send a prompt to Gemini and handle all error cases
        
        Args:
            prompt: The prompt to send to Gemini
            max_tokens: Maximum tokens for the response
            
        Returns:
            str: The response text, or None if failed
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=max_tokens,
                )
            )
            
            if not response.candidates:
                print(f"No response candidates returned during Gemini API call")
                return None
                
            candidate = response.candidates[0]
            if candidate.finish_reason != 1:  # 1 = STOP (successful completion)
                finish_reasons = {
                    0: "FINISH_REASON_UNSPECIFIED",
                    1: "STOP", 
                    2: "MAX_TOKENS",
                    3: "SAFETY",
                    4: "RECITATION"
                }
                reason = finish_reasons.get(candidate.finish_reason, f"Unknown ({candidate.finish_reason})")
                print(f"Gemini response failed. Finish reason: {reason}")
                return None
            
            if not candidate.content or not candidate.content.parts:
                print(f"Gemini response has no content parts")
                return None
                
            return candidate.content.parts[0].text.strip()
            
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
            return None
    
    def _create_classification_prompt(self, email_subject: str) -> Optional[str]:
        """Create prompt for email classification"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, '..', 'prompt_templates', 'classification_template.txt')
            
            with open(template_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            return prompt_template.format(email_subject=email_subject)
        except FileNotFoundError:
            print("Error: classification_template.txt not found")
            return None

    def _create_batch_classification_prompt(self, subjects: List[str]) -> Optional[str]:
        """Create prompt for batch classification of email subjects"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, '..', 'prompt_templates', 'batch_classification_template.txt')
            
            with open(template_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            subjects_list = ""
            for i, subject in enumerate(subjects, 1):
                subjects_list += f"{i}. {subject}\n"
            
            return prompt_template.format(email_subjects_list=subjects_list)
        except FileNotFoundError:
            print("Error: batch_classification_template.txt not found")
            return None
    
    def _create_extraction_prompt(self, email_subject: str, email_sender: str, email_body: str) -> Optional[str]:
        """Create prompt for job application info extraction"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.join(script_dir, '..', 'prompt_templates', 'extraction_template.txt')
            
            with open(template_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            return prompt_template.format(
                email_subject=email_subject,
                email_sender=email_sender,
                email_body=email_body[:1500]
            )
        except FileNotFoundError:
            print("Error: extraction_template.txt not found")
            return None

    def classify_email(self, email_subject: str) -> bool:
        """
        Classify if an email subject is related to job applications using Gemini AI
        
        Args:
            email_subject: The subject line of the email
            
        Returns:
            bool: True if the email appears to be job application related, False otherwise
        """
        if not email_subject.strip():
            print("Email subject is empty when trying to classify")
            return False
            
        prompt = self._create_classification_prompt(email_subject)
        if not prompt:
            return False
            
        response_text = self._send_to_gemini(prompt, max_tokens=300)
        
        if not response_text:
            print("No response text when trying to classify")
            return False
            
        is_job_related = "YES" in response_text.upper()
        
        return is_job_related
    
    def filter_emails(self, emails: List[Dict]) -> List[Dict]:
        """
        Filter emails to only return those classified as job-related using Gemini AI
        
        Args:
            emails: List of email dictionaries with 'subject', 'from', 'body', etc.
            
        Returns:
            List[Dict]: List of email dictionaries that are classified as job-related
        """
        if not emails:
            return []
        
        # Extract subjects for batch classification
        email_subjects = [email.get('subject', '') for email in emails]
        
        batch_prompt = self._create_batch_classification_prompt(email_subjects)
        if not batch_prompt:
            return []
        
        response_text = self._send_to_gemini(batch_prompt, max_tokens=4000)
        
        if not response_text:
            print("No response text for batch classification")
            return []
        
        classifications = self._parse_batch_classification_response(response_text, len(email_subjects))
        
        # Filter emails based on classifications
        job_related_emails = []
        for email, is_job_related in zip(emails, classifications):
            if is_job_related:
                job_related_emails.append(email)
        
        return job_related_emails
    
    def _parse_batch_classification_response(self, response: str, expected_count: int) -> List[bool]:
        """Parse the batch classification response into a list of boolean values"""
        try:
            lines = [line.strip().upper() for line in response.strip().split('\n') if line.strip()]
            
            results = []
            for line in lines:
                if 'YES' in line:
                    results.append(True)
                else:
                    results.append(False)
            
            while len(results) < expected_count:
                results.append(False)
            
            return results[:expected_count]
            
        except Exception as e:
            print(f"Error parsing batch classification response: {e}")
            return [False] * expected_count

    def extract_email_data(self, email_data: Dict) -> Optional[JobApplication]:
        """Parse single email using Gemini AI"""
        
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender = email_data.get('from', '')
        
        prompt = self._create_extraction_prompt(subject, sender, body)
        if not prompt:
            return None
            
        response_text = self._send_to_gemini(prompt, max_tokens=1000)
        
        if not response_text:
            return None
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if not json_match:
                print("No JSON found in response")
                return None
                
            data = json.loads(json_match.group(0))
            
            # Validate required fields
            if not all(key in data for key in ['company_name', 'position_title', 'status']):
                print("Missing required fields in response")
                return None
            
            job_app = JobApplication(
                company_name=data['company_name'].strip(),
                position_title=data['position_title'].strip(),
                status=data['status'].strip(),
                is_job_application_update=data.get('is_job_application_update', 'no').strip().lower() == 'yes',
                confidence=float(data.get('confidence', 0.8))
            )
            
            return job_app
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None
        except Exception as e:
            print(f"Error processing extraction result: {e}")
            return None