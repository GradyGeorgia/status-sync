from models import JobApplicationStatus

email_data_list_1 = [
    JobApplicationStatus(
        company_name="Medline",
        position_title="IS Developer",
        status="applied",
        is_job_application_update=True,
        position_location="Madison, WI",
        action_date="unknown"
    ),
    JobApplicationStatus(
        company_name="HNI Corporation",
        position_title="Intern Information Technologies",
        status="applied",
        is_job_application_update=True,
        position_location="unknown",
        action_date="unknown"
    ),
    JobApplicationStatus(
        company_name="MISO",
        position_title="Internship Cyber Security",
        status="applied",
        is_job_application_update=True,
        position_location="unknown",
        action_date="unknown"
    )
]

email_data_list_2 = [
    JobApplicationStatus(
        company_name="HNI Corporation",
        position_title="Intern Information Technologies",
        position_location="Muscatine, IA",
        status="interview_scheduled",
        action_date="10/15/2023 2:00 pm",
        is_job_application_update=True
    ),
    JobApplicationStatus(
        company_name="MISO",
        position_title="Internship Cyber Security",
        position_location="unknown",
        status="rejected",
        action_date="unknown",
        is_job_application_update=True
    )
]

email_data_list_3 = [
    JobApplicationStatus(
        company_name="Medline",
        position_title="IS Developer",
        position_location="Madison, WI",
        status="rejected",
        action_date="unknown",
        is_job_application_update=True
    ),
    JobApplicationStatus(
        company_name="HNI Corporation",
        position_title="Intern Information Technologies",
        position_location="Muscatine, IA",
        status="offer",
        action_date="11/01/2023 5:00 pm",
        is_job_application_update=True
    ),
]