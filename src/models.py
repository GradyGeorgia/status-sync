from dataclasses import dataclass

@dataclass
class Email:
    subject: str
    body: str
    sender: str
    recipient: str = ""
    date: str = ""
    
    def __post_init__(self):
        self.subject = self.subject.strip() if self.subject else ""
        self.body = self.body.strip() if self.body else ""
        self.sender = self.sender.strip() if self.sender else ""
        self.recipient = self.recipient.strip() if self.recipient else ""

@dataclass
class JobApplication:
    company_name: str
    position_title: str
    status: str
    is_job_application_update: bool = False
    confidence: float = 0.0

    def get_unique_key(self) -> str:
        return f"{self.company_name.strip().lower()}|{self.position_title.strip().lower()}"
