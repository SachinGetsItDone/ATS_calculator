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

def _call_groq(client: Groq, system_prompt: str, user_prompt: str) -> Dict:
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()

def _try_parse_json(text: str) -> Dict | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):

        # Remove opening fence (```json or ```)
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
        # Remove closing fence
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    
   
def parse_resume(raw_text: str)->Dict:

    client=_get_client()
    prompt=RESUME_USER_PROMPT.format(raw_text=raw_text)
    raw_response=_call_groq(client, RESUME_SYSTEM_PROMPT, prompt)
    result=_try_parse_json(raw_response)

    if result is None:
        return _validate_resume_result(result)
    

    logger.warning("Groq resume parse: first attempt returned invalid JSON, retrying...")
    strict_prompt = (
        "Your previous response was not valid JSON. "
        "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
        + prompt
    )
    raw_response = _call_groq(client, RESUME_SYSTEM_PROMPT, strict_prompt)
    result = _try_parse_json(raw_response)
    if result is not None:
        return _validate_resume_result(result)

    raise ValueError(
        f"Groq returned unparseable response after retry. Raw response:\n{raw_response[:500]}"
    )
    
JD_SYSTEM_PROMPT = (
    "You are a job description parser. Extract information and "
    "return ONLY a valid JSON object. No explanation, no markdown."
)

JD_USER_PROMPT = """Extract the following from this job description and return as JSON:
{{
  "job_title": "",
  "required_skills": ["list of must-have skills"],
  "preferred_skills": ["list of nice-to-have skills"],
  "experience_required": "",
  "education_required": "",
  "key_responsibilities": ["list of responsibilities"],
  "keywords": ["important keywords and phrases for ATS matching"]
}}

Important instructions:
- required_skills: skills explicitly stated as required or must-have.
- preferred_skills: skills stated as preferred, nice-to-have, or bonus.
- keywords: extract ALL important terms an ATS system would match against,
  including skills, technologies, certifications, and domain terms.
- Return ONLY valid JSON. No markdown code fences, no explanation.

Job Description Text:
{raw_text}"""


#it will make sure, that the parse json has all the valid fields we expect
def _validate_jd_result(result: dict) -> dict:
    
    defaults = {
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "experience_required": "",
        "education_required": "",
        "key_responsibilities": [],
        "keywords": [],
    }

    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default
    return result

