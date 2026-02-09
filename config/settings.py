import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Load Environment Variables
# We resolve the parent path to find .env even if running from a subdir
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    """
    Centralized configuration management.
    Validates critical keys on startup to prevent runtime errors.
    """
    
    # --- General Identity ---
    # Now fully dynamic based on your .env
    APP_NAME: str = os.getenv("PROJECT_NAME", "OpsSwarm Autonomous SRE")
    APP_VERSION: str = os.getenv("VERSION", "1.0.0")
    DEBUG_MODE: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # --- LLM Configuration ---
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = "llama-3-70b-versatile"
    TEMPERATURE: float = 0.0
    
    # --- Observability (LangSmith) ---
    # We don't need to read these into variables as LangChain 
    # detects them automatically from os.environ, but we validte them here.
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY")
    ENABLE_TRACING: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    # --- Paths ---
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    SRC_DIR: Path = BASE_DIR / "src"
    MCP_SERVER_SCRIPT: Path = SRC_DIR / "mcp_server.py"
    RAILS_CONFIG_PATH: Path = BASE_DIR / "config" / "rails"

    def __init__(self):
        """Validation Logic: Fail Fast"""
        
        # 1. Check for LLM Key
        if not self.GROQ_API_KEY:
            raise ValueError(
                "CRITICAL ERROR: 'GROQ_API_KEY' is missing in .env.\n"
                "Get one here: https://console.groq.com/"
            )
            
        # 2. Check for Tracing (Optional but recommended to warn)
        if self.DEBUG_MODE and not self.LANGCHAIN_API_KEY:
            print("WARNING: Debug mode is ON but LangSmith API Key is missing.")
            print("   Tracing will not work. Set 'LANGCHAIN_API_KEY' to fix.")

        # 3. Check for MCP Script
        if not self.MCP_SERVER_SCRIPT.exists():
             raise FileNotFoundError(
                f"CRITICAL ERROR: MCP Server script not found at:\n"
                f"{self.MCP_SERVER_SCRIPT}"
            )

# Instantiate singleton
settings = Settings()