from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models import User


async def current_user(
    access_token: str | None = Cookie(default=None), db: Session = Depends(get_db)
) -> User:
    user_id = decode_token(access_token or "")
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user
