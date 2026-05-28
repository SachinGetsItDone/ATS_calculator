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

