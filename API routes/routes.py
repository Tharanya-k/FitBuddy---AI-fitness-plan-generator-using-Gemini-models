import os
from urllib.parse import parse_qs
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import (
    SessionLocal,
    User,
    WorkoutPlan,
    save_user,
    save_plan,
    update_plan,
    get_original_plan,
    get_user,
    delete_user,
)
from app.schemas import UserInput, WorkoutRequest, FeedbackRequest
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan

# Router definition
router = APIRouter()

# Template directory resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURRENT_DIR)
TEMPLATE_DIR = os.path.join(PROJECT_DIR, "templates")

if not os.path.exists(TEMPLATE_DIR):
    TEMPLATE_DIR = os.path.join(CURRENT_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATE_DIR)


def render_template(request: Request, name: str, context: dict = None) -> HTMLResponse:
    """
    Renders templates compatibly across all versions of FastAPI/Starlette
    (handles Starlette 0.36+ signature change).
    """
    ctx = {"request": request}
    if context:
        ctx.update(context)

    try:
        # Starlette 0.36+ / FastAPI 0.108+ style
        return templates.TemplateResponse(request=request, name=name, context=ctx)
    except TypeError:
        # Legacy Starlette style
        return templates.TemplateResponse(name, ctx)


async def _parse_form_body(request: Request) -> dict:
    """
    Parses form data using standard library urllib.parse.
    Eliminates dependency on python-multipart.
    """
    body_bytes = await request.body()
    parsed = parse_qs(body_bytes.decode("utf-8", errors="replace"))
    return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}


# ==========================================
# Web UI Routes (HTML + Jinja2)
# ==========================================

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Renders the homepage form (index.html) for collecting user details.
    """
    return render_template(request, "index.html")


@router.post("/generate-workout", response_class=HTMLResponse)
async def generate_workout(request: Request):
    """
    Captures user input from HTML form, generates 7-day workout plan and nutrition tip,
    persists records in SQLite, and renders the result page.
    """
    form_data = await _parse_form_body(request)

    username = form_data.get("username", "Fitness Enthusiast")
    try:
        user_id = int(form_data.get("user_id", 1))
    except (ValueError, TypeError):
        user_id = 1

    try:
        age = int(form_data.get("age", 25))
    except (ValueError, TypeError):
        age = 25

    try:
        weight = float(form_data.get("weight", 70.0))
    except (ValueError, TypeError):
        weight = 70.0

    goal = form_data.get("goal", "general fitness")
    intensity = form_data.get("intensity", "Medium")

    user_input = {
        "username": username,
        "user_id": user_id,
        "age": age,
        "weight": weight,
        "goal": goal,
        "intensity": intensity
    }

    # Generate AI Workout Plan & Nutrition Tip
    workout_plan = generate_workout_gemini(user_input)
    nutrition_tip = generate_nutrition_tip_with_flash(goal)

    # Persist in SQLite
    save_user(
        user_id=user_id,
        name=username,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity
    )
    save_plan(user_id=user_id, plan=workout_plan)

    return render_template(request, "result.html", {
        "username": username,
        "user_id": user_id,
        "age": age,
        "weight": weight,
        "goal": goal,
        "intensity": intensity,
        "workout_plan": workout_plan,
        "nutrition_tip": nutrition_tip,
        "update_success": False
    })


@router.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(request: Request):
    """
    Processes user feedback to update existing workout plan via Gemini 1.5 Pro.
    """
    form_data = await _parse_form_body(request)
    try:
        user_id = int(form_data.get("user_id", 0))
    except (ValueError, TypeError):
        user_id = 0

    feedback = form_data.get("feedback", "")

    original_plan = get_original_plan(user_id)
    user = get_user(user_id)

    if not original_plan or not user:
        return render_template(request, "result.html", {
            "username": "User",
            "user_id": user_id,
            "age": "N/A",
            "weight": "N/A",
            "goal": "N/A",
            "intensity": "N/A",
            "workout_plan": f"Original plan not found for User ID {user_id}. Please generate a new plan from the homepage first.",
            "nutrition_tip": "Stay consistent with your daily hydration and nutrient intake.",
            "error_message": f"User ID {user_id} does not have an existing plan saved."
        })

    # Update plan via Gemini Pro
    updated_plan_text = update_workout_plan(original_plan, feedback)
    update_plan(user_id, updated_plan_text)

    # Refresh or fetch nutrition tip
    nutrition_tip = generate_nutrition_tip_with_flash(user.goal)

    return render_template(request, "result.html", {
        "username": user.name,
        "user_id": user.id,
        "age": user.age,
        "weight": user.weight,
        "goal": user.goal,
        "intensity": user.intensity,
        "workout_plan": updated_plan_text,
        "original_plan": original_plan,
        "nutrition_tip": nutrition_tip,
        "update_success": True,
        "feedback_submitted": feedback
    })


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request):
    """
    Admin dashboard displaying all registered users and their original & updated plans.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        user_data = []
        for user in users:
            plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user.id).first()
            user_data.append({
                "id": user.id,
                "name": user.name,
                "age": user.age,
                "weight": user.weight,
                "goal": user.goal,
                "intensity": user.intensity,
                "original_plan": plan.original_plan if plan and plan.original_plan else "N/A",
                "updated_plan": plan.updated_plan if plan and plan.updated_plan else "Not updated"
            })
        return render_template(request, "all_users.html", {
            "users": user_data
        })
    finally:
        db.close()


@router.post("/delete-user/{user_id}")
def delete_user_route(user_id: int):
    """
    Admin endpoint to delete a user and redirect back to the user list.
    """
    delete_user(user_id)
    return RedirectResponse(url="/view-all-users", status_code=status.HTTP_303_SEE_OTHER)


# ==========================================
# REST API Endpoints
# ==========================================

@router.post("/generate-workout/gemini")
async def generate_gemini_workout(request: WorkoutRequest):
    """API endpoint to generate workout plan given goal and intensity."""
    try:
        result = generate_workout_gemini({
            "goal": request.goal,
            "intensity": request.intensity
        })
        return {"model": "gemini-pro", "workout_plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nutrition-tip")
def get_flash_tip(goal: str):
    """API endpoint to generate nutrition/recovery tip using Gemini Flash."""
    tip = generate_nutrition_tip_with_flash(goal)
    return {"goal": goal, "nutrition_tip": tip}


@router.post("/generate-plan")
def generate_plan(user_data: UserInput):
    """API endpoint to save user info, generate plan, and persist to SQLite."""
    try:
        save_user(
            user_id=user_data.user_id,
            name=user_data.username,
            age=user_data.age,
            weight=user_data.weight,
            goal=user_data.goal,
            intensity=user_data.intensity
        )

        plan = generate_workout_gemini({
            "goal": user_data.goal,
            "intensity": user_data.intensity
        })

        save_plan(user_data.user_id, plan)

        nutrition_tip = generate_nutrition_tip_with_flash(user_data.goal)

        return {
            "message": "Workout plan generated and saved successfully!",
            "workout_plan": plan,
            "nutrition_tip": nutrition_tip
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong: {str(e)}")


@router.post("/update-plan/{user_id}", response_model=dict)
def update_user_plan(user_id: int, data: FeedbackRequest):
    """API endpoint to update user plan based on feedback."""
    original = get_original_plan(user_id)
    if not original:
        return {"error": "Original plan not found for this user."}

    updated = update_workout_plan(original, data.feedback)
    update_plan(user_id, updated)
    return {"updated_plan": updated}


@router.get("/api/users")
def get_all_users_api():
    """API endpoint returning all registered users and their workout plans."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        results = []
        for u in users:
            plan = db.query(WorkoutPlan).filter_by(user_id=u.id).first()
            results.append({
                "id": u.id,
                "name": u.name,
                "age": u.age,
                "weight": u.weight,
                "goal": u.goal,
                "intensity": u.intensity,
                "original_plan": plan.original_plan if plan else None,
                "updated_plan": plan.updated_plan if plan else None
            })
        return {"total": len(results), "users": results}
    finally:
        db.close()