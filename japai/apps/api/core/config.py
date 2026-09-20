from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent.parent.parent  # japai root
_PARENT_ROOT = _PROJECT_ROOT.parent  # workspace root

_ENV_FILES = [
    str(_PROJECT_ROOT / ".env"),
    str(_PARENT_ROOT / ".env"),
    ".env",
]


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://ja_assure:ja_assure@localhost:5432/ja_assure"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    FIRECRAWL_API_KEY: str = ""
    GOOGLE_PLACES_API_KEY: str = ""
    HUNTER_API_KEY: str = ""
    BUFFER_API_KEY: str = ""

    # --- Live judge demo guards (Phase 10) ---
    DEMO_DAILY_CALL_CEILING: int = 250
    DEMO_CALL_MARGIN: int = 15
    DEMO_RATE_LIMIT_RUNS: int = 5
    DEMO_RATE_LIMIT_WINDOW_SECONDS: int = 120

    model_config = SettingsConfigDict(env_file=_ENV_FILES, extra="ignore")


settings = Settings()

