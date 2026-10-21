"""Single place for configuration; paths do not depend on the terminal's cwd."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_PATH = DATA_DIR / 'docusphere.sqlite3'
CHROMA_DIR = DATA_DIR / 'chroma'
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-mpnet-base-v2')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
JWT_SECRET = os.getenv('JWT_SECRET', '')
COSINE_DISTANCE_CUTOFF = float(os.getenv('COSINE_DISTANCE_CUTOFF', '0.65'))
# Number of semantic candidates checked before final answer generation.
RETRIEVAL_K = max(1, min(15, int(os.getenv('RETRIEVAL_K', '8'))))
ENABLE_QUERY_REWRITE = os.getenv('ENABLE_QUERY_REWRITE', 'false').lower() == 'true'
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_WEB_BYTES = 1 * 1024 * 1024
MAX_CHUNKS_PER_DOC = 2500
