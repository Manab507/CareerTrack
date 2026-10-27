"""
CareerTrack — FastAPI Dependencies
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import decode_access_token
from .database import get_cursor


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT and return user dict (with role)"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(401, "Invalid token: missing subject")
    
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, name, email, role FROM users WHERE id = %s",   # ← role add
            (int(user_id_str),)
        )
        row = cur.fetchone()
    
    if row is None:
        raise HTTPException(401, "User no longer exists")
    
    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "role": row[3] if len(row) > 3 else "user",   # ← role add
    }
def get_current_admin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Verify user is admin.
    Calls get_current_user first, then checks role.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user