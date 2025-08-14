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
    
    def create_extraction_prompt(self, email_subject: str, email_sender: str, email_body: str) -> str:
        """Create prompt for Gemini AI to extract job application info"""
        try:
            with open('prompt_template.txt', 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            return prompt_template.format(
                email_subject=email_subject,
                email_sender=email_sender,
                email_body=email_body[:1500]
            )
        except FileNotFoundError:
            print("Error: prompt not found")

    def parse_email(self, email_data: Dict) -> Optional[JobApplication]:
        """Parse single email using Gemini AI"""
        
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender = email_data.get('from', '')
        
        try:
            prompt = self.create_extraction_prompt(subject, sender, body)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=500,
                )
            )
            
            if not response.candidates:
                print("No response candidates")
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
                print(f"Error: Response incomplete with finish reason: {reason}")
                return None
            
            if not candidate.content or not candidate.content.parts:
                print("Response has no content parts")
                return None 
            response_text = candidate.content.parts[0].text.strip()
            
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if not json_match:
                print("No JSON found in response")
                return None
            data = json.loads(json_match.group(0))
            
            if not all(key in data for key in ['company_name', 'position_title', 'status']):
                print("Missing required fields in response")
                return None
            
            job_app = JobApplication(
                company_name=data['company_name'].strip(),
                position_title=data['position_title'].strip(),
                status=data['status'].strip(),
                confidence=float(data.get('confidence', 0.8))
            )
            
            return job_app
            
        except Exception as e:
            print(f"Error parsing email: {e}")
            return None