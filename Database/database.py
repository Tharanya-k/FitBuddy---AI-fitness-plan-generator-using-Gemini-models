import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fitbuddy.db")

# SQLite connection configuration
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """
    SQLAlchemy Model representing a registered fitness user.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String(255), nullable=False)
    intensity = Column(String(50), nullable=False)
    schedule = Column(Integer, default=7)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to workout plans
    plans = relationship("WorkoutPlan", back_populates="user", cascade="all, delete-orphan")


class WorkoutPlan(Base):
    """
    SQLAlchemy Model representing the AI-generated and updated workout plans for a user.
    """
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_plan = Column(Text, nullable=False)
    updated_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="plans")


# Create tables in the database automatically
Base.metadata.create_all(bind=engine)


# Helper Functions

def get_db():
    """Dependency helper to yield database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_user(user_id: int, name: str, age: int, weight: float, goal: str, intensity: str) -> User:
    """
    Saves a new user or updates existing user details in SQLite database.
    """
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(id=user_id).first()
        if existing:
            existing.name = name
            existing.age = age
            existing.weight = weight
            existing.goal = goal
            existing.intensity = intensity
            user_obj = existing
        else:
            user_obj = User(
                id=user_id,
                name=name,
                age=age,
                weight=weight,
                goal=goal,
                intensity=intensity,
                schedule=7,
            )
            db.add(user_obj)
        db.commit()
        db.refresh(user_obj)
        return user_obj
    finally:
        db.close()


def save_plan(user_id: int, plan: str) -> WorkoutPlan:
    """
    Stores the initial AI-generated 7-day workout plan for a user.
    """
    db = SessionLocal()
    try:
        existing_plan = db.query(WorkoutPlan).filter_by(user_id=user_id).first()
        if existing_plan:
            existing_plan.original_plan = plan
            existing_plan.updated_plan = None
            plan_obj = existing_plan
        else:
            plan_obj = WorkoutPlan(
                user_id=user_id,
                original_plan=plan,
                updated_plan=None
            )
            db.add(plan_obj)
        db.commit()
        db.refresh(plan_obj)
        return plan_obj
    finally:
        db.close()


def update_plan(user_id: int, updated_text: str) -> WorkoutPlan | None:
    """
    Updates the plan based on user feedback, preserving the original version.
    """
    db = SessionLocal()
    try:
        workout = db.query(WorkoutPlan).filter_by(user_id=user_id).first()
        if workout:
            workout.updated_plan = updated_text
            workout.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(workout)
            return workout
        return None
    finally:
        db.close()


def get_original_plan(user_id: int) -> str | None:
    """
    Fetches the original plan for a given user.
    """
    db = SessionLocal()
    try:
        plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id).first()
        return plan.original_plan if plan else None
    finally:
        db.close()


def get_user(user_id: int) -> User | None:
    """
    Retrieves user record by user_id.
    """
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def get_all_users() -> list[User]:
    """
    Retrieves all registered users.
    """
    db = SessionLocal()
    try:
        return db.query(User).all()
    finally:
        db.close()


def get_all_plans() -> list[WorkoutPlan]:
    """
    Retrieves all workout plans.
    """
    db = SessionLocal()
    try:
        return db.query(WorkoutPlan).all()
    finally:
        db.close()


def delete_user(user_id: int) -> bool:
    """
    Deletes a user and their associated workout plans from the database.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    finally:
        db.close()