from fastapi import APIRouter, HTTPException, Depends
from ..database import get_cursor
from ..schemas import UserCreate, UserUpdate
from ..security import hash_password
from ..dependencies import get_current_user, get_current_admin

router = APIRouter(tags=["Users"])

@router.get("/users")
def get_users():
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, email FROM users ORDER BY id")
            users = cur.fetchall()
        return [{"id": u[0], "name": u[1], "email": u[2]} for u in users]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/users")
def create_user(user: UserCreate):
    try:
        hashed_password = hash_password(user.password)
        with get_cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id, name, email",
                (user.name, user.email, hashed_password),
            )
            new_user = cur.fetchone()
        return {"id": new_user[0], "name": new_user[1], "email": new_user[2]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users/{user_id}")
def get_user(user_id: int):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user[0], "name": user[1], "email": user[2]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    try:
        with get_cursor() as cur:
            cur.execute(
                "UPDATE users SET name = %s, email = %s WHERE id = %s RETURNING id, name, email",
                (user.name, user.email, user_id),
            )
            updated_user = cur.fetchone()
        if updated_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User updated successfully", "user": {"id": updated_user[0], "name": updated_user[1], "email": updated_user[2]}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/users/{user_id}")
def delete_user(user_id: int):
    try:
        with get_cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id, name, email", (user_id,))
            deleted_user = cur.fetchone()
        if deleted_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully", "deleted_user": {"id": deleted_user[0], "name": deleted_user[1], "email": deleted_user[2]}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "name": current_user["name"], "email": current_user["email"]}

@router.get("/admin/users")
def admin_get_all_users(admin: dict = Depends(get_current_admin)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, email, role FROM users ORDER BY id")
            users = cur.fetchall()
        return [{"id": u[0], "name": u[1], "email": u[2], "role": u[3]} for u in users]
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin: dict = Depends(get_current_admin)):
    try:
        if user_id == admin["id"]:
            raise HTTPException(400, "Cannot delete yourself")
        with get_cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s RETURNING id, name, email", (user_id,))
            deleted = cur.fetchone()
        if deleted is None:
            raise HTTPException(404, "User not found")
        return {"message": "User deleted by admin", "deleted_user": {"id": deleted[0], "name": deleted[1], "email": deleted[2]}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))