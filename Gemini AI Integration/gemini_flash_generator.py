import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL_NAME = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash")

# Check if google.generativeai SDK is installed, else use built-in REST API
try:
    import google.generativeai as genai
    if API_KEY and API_KEY != "your_gemini_api_key_here":
        genai.configure(api_key=API_KEY)
    HAS_GENAI_LIB = True
except ImportError:
    HAS_GENAI_LIB = False


def _call_gemini_flash_rest_api(prompt: str, model: str = MODEL_NAME) -> str:
    """Calls Gemini Flash official REST API using Python standard library."""
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
    with urllib.request.urlopen(req, timeout=30) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        candidates = res_data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
    return _fallback_nutrition_tip("")


def generate_nutrition_tip_with_flash(goal: str) -> str:
    """
    Generate a nutrition or recovery tip using Gemini Flash based on the user's fitness goal.
    Supports both SDK and direct standard library REST API.
    """
    prompt = (
        f"Give one clear, helpful nutrition or recovery tip for someone focused on '{goal}'. "
        "The tip should be practical, friendly, and easy to understand."
    )

    if not API_KEY or API_KEY == "your_gemini_api_key_here":
        return _fallback_nutrition_tip(goal)

    if HAS_GENAI_LIB:
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[Gemini Flash SDK Notice]: {e}, falling back to REST API...")

    try:
        return _call_gemini_flash_rest_api(prompt, MODEL_NAME)
    except Exception as e:
        print(f"[Gemini Flash REST API Error]: {e}")
        return _fallback_nutrition_tip(goal)


def _fallback_nutrition_tip(goal: str) -> str:
    goal_lower = goal.lower() if goal else "general fitness"
    if "muscle" in goal_lower or "bulk" in goal_lower or "gain" in goal_lower:
        return (
            "Prioritize protein! Aim for 1.6 to 2.2 grams of protein per kilogram of body weight daily "
            "(chicken, fish, eggs, tofu, Greek yogurt). Pair your post-workout meal with complex carbohydrates "
            "to replenish glycogen stores and trigger optimal muscle synthesis."
        )
    elif "loss" in goal_lower or "fat" in goal_lower or "cut" in goal_lower:
        return (
            "Focus on high-volume, nutrient-dense foods! Fill half your plate with leafy greens and fibrous vegetables. "
            "Drink at least 3 liters of water throughout the day, and drink a glass of water 20 minutes before meals "
            "to enhance satiety and boost your metabolic rate."
        )
    elif "flexibility" in goal_lower or "mobility" in goal_lower:
        return (
            "Stay thoroughly hydrated and consume anti-inflammatory foods rich in Omega-3 fatty acids "
            "(salmon, walnuts, chia seeds). Magnesium-rich foods like spinach and pumpkin seeds will also help "
            "prevent muscle tightness and enhance joint mobility."
        )
    else:
        return (
            "Balance and consistency are key! Combine lean proteins, colorful vegetables, and healthy fats at every meal. "
            "Ensure you get 7-8 hours of quality sleep each night—true fitness gains and cellular recovery happen while resting."
        )