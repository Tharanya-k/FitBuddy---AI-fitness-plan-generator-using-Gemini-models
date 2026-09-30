from pydantic import BaseModel, Field
from typing import Optional


class UserInput(BaseModel):
    """
    Schema for capturing user details and fitness parameters.
    """
    user_id: int = Field(..., description="Unique User Identifier", example=10)
    username: str = Field(..., description="Full Name or Username", example="Alex Morgan")
    age: int = Field(..., ge=10, le=120, description="Age in years", example=25)
    weight: float = Field(..., gt=0, description="Weight in kilograms", example=70.5)
    goal: str = Field(..., description="Fitness Goal (e.g., muscle gain, weight loss)", example="muscle gain")
    intensity: str = Field(..., description="Workout Intensity: Low, Medium, High", example="High")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 101,
                "username": "Alex Morgan",
                "age": 25,
                "weight": 70.0,
                "goal": "muscle gain",
                "intensity": "High"
            }
        }


class WorkoutRequest(BaseModel):
    """
    Schema for generating workout plan directly via API.
    """
    goal: str = Field(..., example="muscle gain")
    intensity: str = Field(..., example="high")


class FeedbackRequest(BaseModel):
    """
    Schema for submitting plan update feedback.
    """
    feedback: str = Field(..., example="Please include more upper body strength and reduce cardio.")


class WorkoutPlanResponse(BaseModel):
    """
    API Response model for generated workout plan.
    """
    model: str
    workout_plan: str


class NutritionTipResponse(BaseModel):
    """
    API Response model for nutrition tip.
    """
    goal: str
    nutrition_tip: str


class PlanGenerationResponse(BaseModel):
    """
    Response model after saving user and generating plan.
    """
    message: str
    workout_plan: str
    nutrition_tip: Optional[str] = None