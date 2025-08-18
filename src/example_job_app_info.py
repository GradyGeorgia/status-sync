from models import JobApplication

email_data_list_1 = [
    JobApplication(
        company_name="Medline",
        position_title="IS Developer",
        status="applied",
        is_job_application_update=True,
        confidence=1.0
    ),
    JobApplication(
        company_name="HNI Corporation",
        position_title="Intern Information Technologies",
        status="applied",
        is_job_application_update=True,
        confidence=1.0
    ),
    JobApplication(
        company_name="MISO",
        position_title="Internship Cyber Security",
        status="applied",
        is_job_application_update=True,
        confidence=1.0
    )
]

email_data_list_2 = [
    JobApplication(
        company_name="HNI Corporation",
        position_title="Intern Information Technologies",
        status="interview_scheduled",
        is_job_application_update=True,
        confidence=1.0
    ),
    JobApplication(
        company_name="MISO",
        position_title="Internship Cyber Security",
        status="rejected",
        is_job_application_update=True,
        confidence=1.0
    )
]

email_data_list_3 = [
    JobApplication(
        company_name="Medline",
        position_title="IS Developer",
        status="rejected",
        is_job_application_update=True,
        confidence=1.0
    ),
    JobApplication(
        company_name="HNI Corporation",
        position_title="Intern Information Technologies",
        status="offer",
        is_job_application_update=True,
        confidence=1.0
    ),
]