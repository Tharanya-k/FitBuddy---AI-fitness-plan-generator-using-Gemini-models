from sqlalchemy.orm import Session

from .models import User


def create_user(
    db: Session,
    user_id: str,
    username: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
    original_plan: str,
    nutrition_tip: str,
):
    user = User(
        user_id=user_id,
        username=username,
        age=age,
        weight=weight,
        goal=goal,
        intensity=intensity,
        original_plan=original_plan,
        nutrition_tip=nutrition_tip,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_id(db: Session, user_id: int):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def get_all_users(db: Session):
    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .all()
    )


def update_user_feedback(
    db: Session,
    user_id: int,
    feedback: str,
):
    user = get_user_by_id(db, user_id)

    if user:
        user.feedback = feedback
        db.commit()
        db.refresh(user)

    return user


def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)

    if user:
        db.delete(user)
        db.commit()

    return user