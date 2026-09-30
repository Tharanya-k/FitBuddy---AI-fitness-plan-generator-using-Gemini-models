import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_WORKOUT_MODEL: str = os.getenv(
        "GEMINI_WORKOUT_MODEL",
        "gemini-3.8-flash"
    )
    GEMINI_NUTRITION_MODEL: str = os.getenv(
        "GEMINI_NUTRITION_MODEL",
        "gemini-3.8-flash"
    )


settings = Settings()
