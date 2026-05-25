import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# api metadata
APP_TITLE='ATS RESUME ANALYZER API'
APP_VERSION='1.0.0'
APP_DESCRIPTION=' analysze resumes against job description using nlpt + ml'

ALLOWED_ORIGINS = [
    "https://localhost:5273",
    "https://localhost:3000",
    "https://localhost:5173"
]

# file
MAX_FILE_SIZE_MB=5
MAX_FILE_SIZE_BYTES=MAX_FILE_MB*1024*1024

# Supported MINE types and their short names

SUPPORTED_EXTENSIOSN = {
    '.pdf', '.doc', '.docx'
}

SPACY_MODEL_PRIMARY="en_core_web_md"
SPACY_MODEL_SECONDARY='"en_core_web_sm'
SENTENCE_TRANSFORMER_MODEL = os.getenv(
    "SENTENCE_TRASNFORMER_MODE",
    "ALL-mINIlm-l6-V2"
)


SCORE_WEIGHTS={
    "formating":20,
    "keywords": 25,
    "content": 25,
    "skill_validation": 15,
    "ats_compatibility": 15
}

JD_KEYWORD_WEIGHT=0.6
JD_SEMANTIC_WEIGHT=0.4

SUPABASE_URL       = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY       = os.getenv('SUPABASE_KEY', '')          # service_role — DB writes (bypasses RLS)
SUPABASE_ANON_KEY  = os.getenv('SUPABASE_ANON_KEY', '')     # public anon — frontend auth calls
SUPABASE_JWT_SECRET= os.getenv('SUPABASE_JWT_SECRET', '')   # used by backend to verify access tokens
GROQ_API_KEY       = os.getenv('GROQ_API_KEY', '')
