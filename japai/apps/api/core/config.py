from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://ja_assure:ja_assure@localhost:5432/ja_assure"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    FIRECRAWL_API_KEY: str = ""
    GOOGLE_PLACES_API_KEY: str = ""
    HUNTER_API_KEY: str = ""
    BUFFER_API_KEY: str = ""

    # --- Live judge demo guards (Phase 10) ---
    # DEMO_DAILY_CALL_CEILING is an OPERATIONAL GUESS, not a documented Google
    # limit. We have run 177 calls in a day with zero failures, so the real cap
    # is higher than that; this is a self-imposed budget so a live demo degrades
    # to recorded examples instead of hitting a hard quota error in front of a
    # judge. Raise or lower it in .env without a rebuild.
    DEMO_DAILY_CALL_CEILING: int = 250
    # How close to the ceiling before live mode stops accepting new runs.
    DEMO_CALL_MARGIN: int = 15
    # Per-session rate limit: max runs per window.
    DEMO_RATE_LIMIT_RUNS: int = 5
    DEMO_RATE_LIMIT_WINDOW_SECONDS: int = 120

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
