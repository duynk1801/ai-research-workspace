import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

EVIDENCE_DIR = DATA_DIR / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)

ANALYSIS_DIR = DATA_DIR / "analysis"
ANALYSIS_DIR.mkdir(exist_ok=True)

INDEX_DIR = DATA_DIR / "index"
INDEX_DIR.mkdir(exist_ok=True)

IDEAS_DIR = DATA_DIR / "ideas"
IDEAS_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "knowledge.db"

MIMO_API_KEY = os.getenv("MIMO_API_KEY")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048

MATURITY_LEVELS = {
    "S1": "Raw insight - just extracted, not validated",
    "S2": "Validated - cross-referenced with other sources",
    "S3": "Actionable - has clear next steps"
}
