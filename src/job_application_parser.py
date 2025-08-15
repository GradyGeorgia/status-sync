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
            print("Email subject is empty when trying to classify")
            return False
            
        prompt = self.create_classification_prompt(email_subject)
        response_text = self._send_to_gemini(prompt, max_tokens=300)
        
        if not response_text:
            print("No response text when trying to classify")
            return False
            
        is_job_related = "YES" in response_text.upper()
        
        return is_job_related

    def extract_email_data(self, email_data: Dict) -> Optional[JobApplication]:
        """Parse single email using Gemini AI"""
        
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender = email_data.get('from', '')
        
        prompt = self.create_extraction_prompt(subject, sender, body)
        response_text = self._send_to_gemini(prompt, max_tokens=500)
        
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
            
            return job_app
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None
        except Exception as e:
            print(f"Error processing extraction result: {e}")
            return None

    def classify_email_batch(self, email_subjects: List[str]) -> List[bool]:
        """
        Classify multiple email subjects in a single batch request using Gemini AI
        
        Args:
            email_subjects: List of email subject lines to classify
            
        Returns:
            List[bool]: List of boolean values indicating if each email is job-related
                       Returns False for subjects that couldn't be classified
        """

        if not email_subjects:
            return []
        
        # Filter out empty subjects and keep track of original indices
        valid_subjects = []
        original_indices = []
        
        for i, subject in enumerate(email_subjects):
            if subject and subject.strip():
                valid_subjects.append(subject.strip())
                original_indices.append(i)
        
        if not valid_subjects:
            return [False] * len(email_subjects)
        
        # Create batch prompt
        batch_prompt = self._create_batch_classification_prompt(valid_subjects)
        
        # Send to Gemini with higher token limit for batch response
        response_text = self._send_to_gemini(batch_prompt, max_tokens=4000)
        
        if not response_text:
            print("No response text for batch classification")
            return [False] * len(email_subjects)
        
        # Parse batch response
        results = self._parse_batch_classification_response(response_text, len(valid_subjects))
        
        # Map results back to original indices
        final_results = [False] * len(email_subjects)
        for i, original_idx in enumerate(original_indices):
            if i < len(results):
                final_results[original_idx] = results[i]
        
        return final_results
    
    def _create_batch_classification_prompt(self, subjects: List[str]) -> str:
        """Create a prompt for batch classification of email subjects"""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to the project root, then into prompt_templates
            template_path = os.path.join(script_dir, '..', 'prompt_templates', 'batch_classification_template.txt')
            
            with open(template_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # Create numbered list of subjects
            subjects_list = ""
            for i, subject in enumerate(subjects, 1):
                subjects_list += f"{i}. {subject}\n"
            
            return prompt_template.format(email_subjects_list=subjects_list)
            
        except FileNotFoundError:
            print("Error: prompt_templates/batch_classification_template.txt not found")
            # Fallback to basic prompt if template file is missing
            prompt = "Classify each email subject as job-related (YES) or not (NO):\n\n"
            for i, subject in enumerate(subjects, 1):
                prompt += f"{i}. {subject}\n"
            prompt += "\nResponses (one per line, only YES or NO):\n"
            return prompt
    
    def _parse_batch_classification_response(self, response: str, expected_count: int) -> List[bool]:
        """Parse the batch classification response into a list of boolean values"""
        try:
            lines = [line.strip().upper() for line in response.strip().split('\n') if line.strip()]
            
            results = []
            for line in lines:
                # Look for YES/NO in each line, handling numbered responses
                if 'YES' in line:
                    results.append(True)
                elif 'NO' in line:
                    results.append(False)
            
            # Ensure we have the expected number of results
            while len(results) < expected_count:
                results.append(False)  # Default to False for missing responses
            
            return results[:expected_count]  # Trim if we got too many responses
            
        except Exception as e:
            print(f"Error parsing batch classification response: {e}")
            return [False] * expected_count