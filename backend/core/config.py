import os
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables from .env file
# Root of backend is parent of core
BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_ROOT / ".env")

# Core Paths
CORE_DIR = BACKEND_ROOT / "core"
DATA_DIR = CORE_DIR / "data"
DB_DIR = DATA_DIR / "db"

# Configurable reports directory with fallback
DEFAULT_REPORTS_DIR = "/mnt/p/linux/investment-analyst-agent/data/reports"
REPORTS_DIR_PATH = os.getenv("REPORTS_DIR", DEFAULT_REPORTS_DIR)
REPORTS_DIR = Path(REPORTS_DIR_PATH)

# Ensure directories exist
DB_DIR.mkdir(parents=True, exist_ok=True)
try:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    # Fallback to local core/data/reports if path is unavailable/unmounted
    fallback_path = DATA_DIR / "reports"
    print(f"[!] Warning: Failed to create REPORTS_DIR at {REPORTS_DIR}. Falling back to local: {fallback_path}. Error: {e}")
    REPORTS_DIR = fallback_path
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "your_mysql_password_here")
# If the password is still the template default, treat it as empty or use a blank string
if MYSQL_PASSWORD == "your_mysql_password_here":
    MYSQL_PASSWORD = ""
MYSQL_DB = os.getenv("MYSQL_DB", "investment_db")

# Report Language Configuration
REPORT_LANGUAGE = os.getenv("REPORT_LANGUAGE", "EN").upper()


# Supported Regions & Benchmarks
REGIONS = {
    "US": {
        "name": "美股",
        "benchmark": "^GSPC",  # S&P 500
        "currency": "USD",
        # Sector ETFs to measure sector momentum
        "sector_etfs": {
            "XLK": "科技 (Technology)",
            "XLF": "金融 (Financials)",
            "XLE": "能源 (Energy)",
            "XLV": "醫療保健 (Healthcare)",
            "XLY": "非必須消費 (Consumer Discretionary)",
            "XLI": "工業 (Industrial)",
            "XLP": "必須消費 (Consumer Staples)",
            "XLB": "原物料 (Materials)",
            "XLU": "公用事業 (Utilities)"
        }
    },
    "Taiwan": {
        "name": "台股",
        "benchmark": "^TWII",  # TAIEX
        "currency": "TWD",
        # Taiwan standard tracking ETFs & Sector proxies
        "sector_etfs": {
            "0050.TW": "元大台灣50 (Broad Market)",
            "0052.TW": "富邦科技 (Tech Sector)",
            "0056.TW": "元大高股息 (High Dividend)",
            "2330.TW": "台積電 (Semiconductor Proxy)",
            "2881.TW": "富邦金 (Financials Proxy)",
            "1301.TW": "台塑 (Materials/Old Economy Proxy)"
        }
    }
}

# AI Settings
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"  # Highly efficient for agent loops
WRITER_GEMINI_MODEL = "gemini-2.5-flash"   # Standardized to Flash to respect free tier daily limits
TEMPERATURE = 0.2

# Pipeline Limits (for API quota management)
MAX_SECTORS_PER_REGION = 2  # Default to scan top 2 performing sectors
MAX_STOCKS_PER_REGION = 4   # Default to deep-dive top 4 representative stocks per region

