import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://ja_assure:ja_assure_pw@localhost:5432/ja_assure",
    )

    # Publishing Provider Configuration
    # Mode: "buffer" or "simulation" (auto-falls back to simulation if token is unset or "dummy")
    PUBLISHER_MODE: str = os.getenv("PUBLISHER_MODE", "auto")

    # Buffer Credentials
    BUFFER_ACCESS_TOKEN: str = os.getenv("BUFFER_ACCESS_TOKEN", "")
    BUFFER_PROFILE_ID_LINKEDIN: str = os.getenv("BUFFER_PROFILE_ID_LINKEDIN", "")
    BUFFER_API_URL: str = os.getenv("BUFFER_API_URL", "https://api.bufferapp.com/1")
    BUFFER_GRAPHQL_URL: str = os.getenv("BUFFER_GRAPHQL_URL", "https://api.buffer.com/graphql")

    # Worker Tuning
    POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "10"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "5"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_simulation_mode(self) -> bool:
        """Determines if the publisher should run in simulation mode."""
        mode = self.PUBLISHER_MODE.lower().strip()
        if mode == "simulation" or mode == "mock":
            return True
        if mode == "buffer":
            return False
        # auto: if token is empty or dummy placeholder, simulate
        token = self.BUFFER_ACCESS_TOKEN.strip()
        if not token or token.lower() in ("dummy", "test", "mock", "placeholder", "your_buffer_token_here"):
            return True
        return False


worker_settings = WorkerSettings()
