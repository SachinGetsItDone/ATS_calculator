import os 
import json 
import logging 
from typing import Dict

from groq import Groq

logger = logging.getLogger('ats_resume_scorer')

GROQ_MODEL = 'llama-3.3-70b-versatile'

_client=None

def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key=os.getenv("GROQ_API_KEY")
        if api_key is None:
            raise ValueError("GROQ_API_KEY environment variable not set")
        _client = Groq(api_key=api_key, model=GROQ_MODEL)
        logger.info(f'Initialized GROQ client with model {GROQ_MODEL}')
    return _client

RESUME_SYSTEM_PROMPT = """
You are an expert resume parser. Your task is to extract structured information from resumes in a consistent JSON format. No explanation, no markdown or any other addtional information, just the JSON output.
"""

RESUME_USER_PROMPT = """Extract the following from this resume and return as JSON:
{{
    "name": str,  # Full name of the candidate
    "email": str,  # Email address
    "phone": str,  # Phone number
    "professional_summary": str,  # A brief summary of the candidate's professional background
    "linkdin": str,  # LinkedIn profile URL
    "github": str,  # GitHub profile URL
    "skills": List[str],  # List of skills
    "experience": List[{{  # List of work experiences
        "company": str,  # Company name
        "title": str,    # Job title
        "start_date": str,  # Start date (e.g. "Jan 2020")
        "end_date": str,    # End date (e.g. "Present" or "Dec 2022")
        "description": str   # Description of responsibilities and achievements
        "duration_in_months": int  # Duration of the job in months
    }}],
    "education": List[{{  # List of educational qualifications
        "institution": str,  # Name of the institution
        "degree": str,       # Degree obtained
        "field_of_study": str,  # Field of study
        "start_date": str,   # Start date (e.g. "Sep 2015")
        "end_date": str      # End date (e.g. "Jun 2019")
    }}]
    "certifications": List["list of certifications"],  # List of certifications
    "projects": List[{{  # List of projects
        "name": str,  # Project name
        "description": str,  # Brief description of the project
        "technologies": List[str]  # List of technologies used in the project
    }}]
    "action_verbs": List[str]  # List of action verbs used in the resume
    "keywords": List[str]  # List of keywords relevant to the candidate's skills and experience
}}

Important instructions:
- For duration_in_months, calculate the total number of months between start_date and end_date. If end_date is "Present", use the current date for calculation.
- For skills, extract All technical and soft skills mentioned in the resume. Be comprehensive.
- For action_verbs, extract all unique action verbs used in the experience descriptions (e.g. "developed", "led", "managed", etc.)
- For keywords, extract all relevant keywords that are commonly used in job descriptions for the candidate's field (e.g. "machine learning", "project management", "Python", etc.)
- Return ONLY valid JSON. No markdown code fences, no explanations, no additional text. If any information is missing in the resume, use an empty string or an empty list as appropriate.


Resume Text:
{raw_text}"""
