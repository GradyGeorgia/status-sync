import os
import json
import re
from dataclasses import dataclass
from typing import Dict, Optional
import google.generativeai as genai

@dataclass
class JobApplication:
    company_name: str
    position_title: str
    status: str
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
    
    def create_classification_prompt(self, email_subject: str) -> str:
        """Create prompt for email classification"""
        try:
            with open('../prompt_templates/classification_template.txt', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            return prompt_template.format(email_subject=email_subject)
        except FileNotFoundError:
            print("Error: ../prompt_templates/classification_template.txt not found")
    
    def create_extraction_prompt(self, email_subject: str, email_sender: str, email_body: str) -> str:
        """Create prompt for Gemini AI to extract job application info"""
        try:
            with open('../prompt_templates/extraction_template.txt', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            return prompt_template.format(
                email_subject=email_subject,
                email_sender=email_sender,
                email_body=email_body[:1500]
            )
        except FileNotFoundError:
            print("Error: ../prompt_templates/extraction_template.txt not found")

    def classify_email(self, email_subject: str) -> bool:
        """
        Classify if an email subject is related to job applications using Gemini AI
        
        Args:
            email_subject: The subject line of the email
            
        Returns:
            bool: True if the email appears to be job application related, False otherwise
        """
        if not email_subject.strip():
            return False
            
        prompt = self.create_classification_prompt(email_subject)
        response_text = self._send_to_gemini(prompt, max_tokens=10, operation_name="email classification")
        
        if not response_text:
            return False
            
        is_job_related = "YES" in response_text.upper()
        print(f"Subject classification: {'JOB-RELATED' if is_job_related else 'NOT JOB-RELATED'} - {email_subject[:60]}...")
        
        return is_job_related

    def extract_email_data(self, email_data: Dict) -> Optional[JobApplication]:
        """Parse single email using Gemini AI"""
        
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender = email_data.get('from', '')
        
        print(f"Analyzing: {subject[:50]}...")
        
        prompt = self.create_extraction_prompt(subject, sender, body)
        response_text = self._send_to_gemini(prompt, max_tokens=500, operation_name="email extraction")
        
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
                confidence=float(data.get('confidence', 0.8))
            )
            
            print(f"Extracted: {job_app.company_name} - {job_app.position_title} - {job_app.status}")
            return job_app
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None
        except Exception as e:
            print(f"Error processing extraction result: {e}")
            return None