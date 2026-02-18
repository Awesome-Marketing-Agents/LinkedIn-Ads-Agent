import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Core Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
TOKENS_FILE = BASE_DIR / "tokens.json"
DATABASE_FILE = DATA_DIR / "linkedin_ads.db"

# LinkedIn API Credentials & Settings
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:5000/callback")

# Security
OAUTH_STATE = os.getenv("OAUTH_STATE", "supersecretstate")

DATA_DIR.mkdir(exist_ok=True)
SNAPSHOT_DIR.mkdir(exist_ok=True)
