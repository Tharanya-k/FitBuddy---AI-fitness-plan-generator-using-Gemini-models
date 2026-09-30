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


def _call_gemini_rest_api(prompt: str, model: str = MODEL_NAME) -> str:
    """Calls Gemini official REST API using Python standard library."""
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


def generate_workout_gemini(user_input: dict) -> str:
    """
    Generates a personalized, structured 7-day workout plan using Gemini 1.5 Pro.
    Supports both SDK and direct REST API fallback.
    """
    goal = user_input.get("goal", "general fitness")
    intensity = user_input.get("intensity", "medium")

    prompt = f"""
You are a professional fitness trainer.

Create a personalized, structured 7-day workout plan for someone with the goal of **{goal}**, and prefers **{intensity}** intensity workouts.

Each day must include:
- A warm-up (5-10 mins)
- Main workout (targeted exercises, sets & reps)
- Cooldown or recovery tip

Format:
Day 1:
Warm-up: ...
Main Workout: ...
Cooldown: ...
(Repeat for Day 2-7)
"""

    if not API_KEY or API_KEY == "your_gemini_api_key_here":
        return _fallback_workout_plan(goal, intensity)

    if HAS_GENAI_LIB:
        try:
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[Gemini SDK Notice]: {e}, falling back to direct REST API...")

    try:
        return _call_gemini_rest_api(prompt, MODEL_NAME)
    except Exception as e:
        print(f"[Gemini REST API Error]: {e}")
        return f"Note: Gemini API notice: {e}\n\n--- Fallback Plan Generated ---\n\n" + _fallback_workout_plan(goal, intensity)


def _fallback_workout_plan(goal: str, intensity: str) -> str:
    return f"""## 7-Day Workout Plan for {goal.title()} ({intensity.capitalize()} Intensity)

Day 1: Upper Body Strength
Warm-up (5-10 mins): Jumping jacks (60s), arm circles, dynamic chest openers
Main Workout:
- Barbell Bench Press / Push-ups: 3 sets x 8-12 reps
- Overhead Shoulder Press: 3 sets x 10 reps
- Bent-over Barbell Rows: 3 sets x 10-12 reps
- Dumbbell Bicep Curls: 3 sets x 12 reps
- Tricep Dips / Rope Pushdowns: 3 sets x 12 reps
Cooldown (5 mins): Shoulder and chest doorframe stretch, deep breathing

Day 2: Lower Body & Core
Warm-up (5-10 mins): Bodyweight squats, walking lunges, leg swings
Main Workout:
- Goblet Squats / Barbell Squats: 4 sets x 8-12 reps
- Romanian Deadlifts: 3 sets x 10-12 reps
- Walking Lunges: 3 sets x 12 reps per leg
- Glute Bridges: 3 sets x 15 reps
- Plank: 3 sets x 45-60 seconds
Cooldown (5 mins): Hamstring and quad stretches, pigeon pose

Day 3: Cardiovascular Conditioning & Core
Warm-up (5-10 mins): Light jog / brisk walk, hip openers
Main Workout:
- HIIT Intervals (30s sprint, 30s rest): 8 rounds
- Mountain Climbers: 3 sets x 30 seconds
- Bicycle Crunches: 3 sets x 20 reps
- Russian Twists: 3 sets x 20 reps
Cooldown (5 mins): Light walk, child's pose, torso twists

Day 4: Active Recovery / Rest Day
Warm-up: Gentle mobility work
Main Activity:
- 30-45 minutes brisk nature walk, light cycling, or recreational yoga
Cooldown: Full body foam rolling and 10 minutes progressive relaxation

Day 5: Full Body Push & Pull
Warm-up (5-10 mins): Jump rope, arm sweeps, inchworms
Main Workout:
- Dumbbell Incline Press: 3 sets x 10 reps
- Lat Pulldowns / Pull-ups: 3 sets x 8-10 reps
- Dumbbell Lateral Raises: 3 sets x 12-15 reps
- Bulgarian Split Squats: 3 sets x 10 reps per leg
- Hanging Leg Raises: 3 sets x 12 reps
Cooldown (5 mins): Cobra stretch, lat stretch, calf stretch

Day 6: Lower Body Focus & High Intensity Finish
Warm-up (5-10 mins): High knees, butt kicks, bodyweight hip hinge
Main Workout:
- Leg Press or Front Squats: 3 sets x 10 reps
- Hamstring Curls: 3 sets x 12 reps
- Kettlebell Swings: 4 sets x 15 reps
- Box Jumps or Step-ups: 3 sets x 10 reps
Cooldown (5 mins): Seated forward fold, butterfly stretch

Day 7: Rest & Complete Recovery
Activities:
- Hydrate well, light foam rolling, 15 minutes of guided mindfulness or gentle walk
- Prioritize 8 hours of restful sleep and nutrient-rich meals
"""