from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.models import User
from app.schemas.schemas import LoginRequest

router = APIRouter()

DEFAULT_USERS = [
    {"email": "ceo@shopsmart.com", "password": "demo123", "full_name": "CEO", "role": "CEO", "persona": "CEO"},
    {"email": "marketing@shopsmart.com", "password": "demo123", "full_name": "Marketing Manager", "role": "Marketing Manager", "persona": "Marketing Manager"},
    {"email": "sales@shopsmart.com", "password": "demo123", "full_name": "Sales Manager", "role": "Sales Manager", "persona": "Sales Manager"},
    {"email": "admin@shopsmart.com", "password": "admin123", "full_name": "Admin", "role": "Admin", "persona": "Admin"},
]


def seed_users(db: Session):
    for u in DEFAULT_USERS:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            db.add(User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                full_name=u["full_name"],
                role=u["role"],
                persona=u["persona"],
            ))
    db.commit()


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    seed_users(db)
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "persona": user.persona,
            "is_active": user.is_active,
        },
    }


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    from app.core.security import get_current_user
    from fastapi.security import HTTPAuthorizationCredentials
    users = db.query(User).all()
    return [
        {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "persona": u.persona, "is_active": u.is_active}
        for u in users
    ]


@router.get("/me")
def get_me():
    return {"message": "Use /api/auth/users for user info"}
