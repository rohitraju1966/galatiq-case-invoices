from dotenv import load_dotenv
import os

load_dotenv()

DB_PATH = "data/acme.db"
APPROVAL_THRESHOLD = 10_000
GROK_AI_MODEL = "grok-3"
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
MAX_REVIEW_ROUNDS = 1
MAX_EXTRACTION_ATTEMPTS = 3
IS_DEV = True
