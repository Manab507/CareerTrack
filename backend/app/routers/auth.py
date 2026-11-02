from fastapi import APIRouter, HTTPException, Depends,Request
from ..database import get_cursor
from ..schemas import LoginRequest, RefreshRequest
from ..security import verify_password, create_access_token, create_refresh_token, hash_token, decode_access_token
from ..dependencies import get_current_user
from ..limiter import limiter

router = APIRouter(tags=["Authentication"])
@router.post("/login")
@limiter.limit("5/minute")  # <-- Notun line (1 minute e max 5 bar)
def login_user(request: Request, user: LoginRequest): # <-- Request parameter add korte hobe
    try:
        # ... tomar purono login code ...
        with get_cursor() as cur:
            cur.execute("SELECT id, name, email, password_hash FROM users WHERE email = %s", (user.email,))
            found_user = cur.fetchone()
        if found_user is None:
            raise HTTPException(401, "Invalid email or password")
        if not verify_password(user.password, found_user[3]):
            raise HTTPException(401, "Invalid email or password")

        access_token = create_access_token(found_user[0], expires_minutes=15)
        refresh_token = create_refresh_token(found_user[0])
        refresh_hash = hash_token(refresh_token)

        with get_cursor() as cur:
            cur.execute("UPDATE users SET refresh_token_hash = %s WHERE id = %s", (refresh_hash, found_user[0]))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,
            "user": {"id": found_user[0], "name": found_user[1], "email": found_user[2]},
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(500, "Login failed")

@router.post("/refresh")
def refresh_access_token(data: RefreshRequest):
    payload = decode_access_token(data.refresh_token)
    if not payload:
        raise HTTPException(401, "Invalid refresh token")
    user_id = int(payload["sub"])
    with get_cursor() as cur:
        cur.execute("SELECT refresh_token_hash FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    if not row or row[0] != hash_token(data.refresh_token):
        raise HTTPException(401, "Refresh token revoked")
    new_access = create_access_token(user_id, expires_minutes=15)
    return {"access_token": new_access, "token_type": "bearer", "expires_in": 900}

@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute("UPDATE users SET refresh_token_hash = NULL WHERE id = %s", (current_user["id"],))
    return {"message": "Logged out successfully"}