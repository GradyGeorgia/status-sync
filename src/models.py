from dataclasses import dataclass

@dataclass
class Email:
    subject: str = ""
    body: str = ""
    sender: str = ""
    recipient: str = ""
    date: str = ""
    
    def __post_init__(self):
        self.subject = self.subject.strip() if self.subject else ""
        self.body = self.body.strip() if self.body else ""
        self.sender = self.sender.strip() if self.sender else ""
        self.recipient = self.recipient.strip() if self.recipient else ""

@dataclass
class JobApplicationStatus:
    company_name: str = "unknown"
    position_title: str = "unknown"
    position_location: str = "unknown"
    status: str = "unknown"
    action_date: str = "unknown"
    is_job_application_update: bool = False

    def get_unique_key(self) -> str:
        return f"{self.company_name.strip().lower()}|{self.position_title.strip().lower()}"
