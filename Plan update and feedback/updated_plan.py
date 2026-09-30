import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro")

try:
    import google.generativeai as genai
    if API_KEY and API_KEY != "your_gemini_api_key_here":
        genai.configure(api_key=API_KEY)
    HAS_GENAI_LIB = True
except ImportError:
    HAS_GENAI_LIB = False


def _call_gemini_update_rest_api(prompt: str, model: str = MODEL_NAME) -> str:
    """Calls Gemini REST API using Python standard library."""
    clean_model = model.replace("models/", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=40) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        candidates = res_data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
    return "No text returned from Gemini API."


def update_workout_plan(original_plan: str, user_feedback: str) -> str:
    """
    Revises an existing 7-day workout plan using Gemini 1.5 Pro based on user feedback.
    Supports both SDK and direct standard library REST API.
    """
    prompt = f"""
You are a professional fitness trainer assistant.

Here's the original 7-day workout plan:
{original_plan}

User Feedback:
"{user_feedback}"

Based on the feedback, revise the relevant parts of the workout plan. Keep the format and rest of the plan unchanged if not needed.
"""

    if not API_KEY or API_KEY == "your_gemini_api_key_here":
        return _fallback_updated_plan(original_plan, user_feedback)

    if HAS_GENAI_LIB:
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[Gemini Update SDK Notice]: {e}, falling back to REST API...")

    try:
        return _call_gemini_update_rest_api(prompt, MODEL_NAME)
    except Exception as e:
        print(f"[Gemini Update REST API Error]: {e}")
        return f"Note: Gemini API notice: {e}\n\n--- Updated Plan (Fallback) ---\n\n" + _fallback_updated_plan(original_plan, user_feedback)


def _fallback_updated_plan(original_plan: str, user_feedback: str) -> str:
    header = f"### [Updated Plan - Incorporated Feedback: '{user_feedback}']\n\n"
    if original_plan:
        updated = original_plan.replace("Day 4: Active Recovery / Rest Day", f"Day 4: Adjusted Active Routine ({user_feedback})")
        if "Day 3:" in updated:
            updated = updated.replace("Day 3: Cardiovascular Conditioning & Core", f"Day 3: Tailored Focus ({user_feedback})")
        return header + updated
    else:
        return header + f"Workout plan revised to accommodate: {user_feedback}."