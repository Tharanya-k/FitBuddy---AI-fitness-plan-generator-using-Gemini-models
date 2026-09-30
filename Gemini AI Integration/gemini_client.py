import os

from dotenv import load_dotenv
from google import genai

from .config import settings


load_dotenv()


API_KEY = (
    getattr(settings, "GOOGLE_API_KEY", None)
    or os.getenv("GOOGLE_API_KEY")
    or os.getenv("GEMINI_API_KEY")
)


if not API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. "
        "Please add your Gemini API key to the .env file."
    )


client = genai.Client(api_key=API_KEY)


DEFAULT_MODEL = os.getenv(
    "GEMINI_WORKOUT_MODEL",
    "gemini-3.8-flash"
)


def generate_text(
    prompt: str,
    model: str | None = None,
) -> str:

    selected_model = model or DEFAULT_MODEL

    response = client.models.generate_content(
        model=selected_model,
        contents=prompt,
    )

    if response is None:
        raise RuntimeError("Gemini returned an empty response.")

    text = getattr(response, "text", None)

    if not text:
        raise RuntimeError("Gemini returned no text.")

    return text.strip()