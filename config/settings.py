import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Load Environment Variables
# We explicitly load the .env file to ensure it works even if run from different directories
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    """
    Centralized configuration for the OpsSwarm application.
    Validates critical environment variables on initialization.
    """
    
    # --- General App Settings ---
    APP_NAME: str = "OpsSwarm Autonomous SRE"
    VERSION: str = "1.0.0"
    DEBUG_MODE: bool = os.getenv("DEBUG", "False").lower() == "true"

    # --- LLM Configuration (Groq) ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = "llama-3-70b-versatile"
    TEMPERATURE: float = 0.0
    MAX_TOKENS: int = 1024

    # --- Paths ---
    # Dynamic path resolution ensures the app works on any machine (Windows/Linux/Mac)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SRC_DIR: Path = BASE_DIR / "src"
    MCP_SERVER_SCRIPT: Path = SRC_DIR / "mcp_server.py"
    
    # --- Guardrails Configuration ---
    RAILS_CONFIG_PATH: Path = BASE_DIR / "config" / "rails"

    def __init__(self):
        # Validation: Fail fast if critical keys are missing
        if not self.GROQ_API_KEY:
            raise ValueError(
                "❌ CRITICAL ERROR: GROQ_API_KEY is missing from .env file. "
                "The agent cannot function without it."
            )
        
        if not self.MCP_SERVER_SCRIPT.exists():
            raise FileNotFoundError(
                f"❌ CRITICAL ERROR: MCP Server script not found at {self.MCP_SERVER_SCRIPT}. "
                "Check your project structure."
            )

# Instantiate the settings object to be imported elsewhere
settings = Settings()

# Optional: Print configuration on startup (masked)
if __name__ == "__main__":
    print(f"✅ Configuration Loaded: {settings.APP_NAME}")
    print(f"   - Model: {settings.GROQ_MODEL}")
    print(f"   - Server Script: {settings.MCP_SERVER_SCRIPT}")