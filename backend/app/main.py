from fastapi import FastAPI, HTTPException, Depends, status, Query,Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta, timezone
from .dependencies import get_current_user, get_current_admin, security

from .database import get_cursor, get_connection
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
    decode_access_token,
)
from .dependencies import get_current_user, security
from .schemas import (
    UserCreate,
    UserUpdate,
    LoginRequest,
    RefreshRequest,
    ApplicationCreate,      # ← Day 55
    ApplicationUpdate,      # ← Day 55
    ApplicationResponse, 
     ApplicationStats ,
     CompanyCreate,
     CompanyResponse,
     InterviewCreate,
     InterviewUpdate,
     InterviewResponse,
     UserDashboardStats,
     AdminDashboardStats
       # ← Day 55
)
app = FastAPI()
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the error (pore logging add korbo)
    print(f"❌ Global Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error. Amra eta fix korchi!",
            "detail": str(exc)
        }
    )
from fastapi.responses import JSONResponse


# ==========================================
# Pydantic Models
# ==========================================

class RefreshRequest(BaseModel):
    refresh_token: str


# ==========================================
# GET /users — List all users
# ==========================================

@app.get("/users")
def get_users():
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, email FROM users ORDER BY id")
            users = cur.fetchall()
        return [{"id": u[0], "name": u[1], "email": u[2]} for u in users]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# POST /users — Create user
# ==========================================

@app.post("/users")
def create_user(user: UserCreate):
    try:
        hashed_password = hash_password(user.password)
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, name, email
                """,
                (user.name, user.email, hashed_password),
            )
            new_user = cur.fetchone()
        return {
            "id": new_user[0],
            "name": new_user[1],
            "email": new_user[2],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# GET /users/{user_id} — Get single user
# ==========================================

@app.get("/users/{user_id}")
def get_user(user_id: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT id, name, email FROM users WHERE id = %s",
                (user_id,),
            )
            user = cur.fetchone()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user[0], "name": user[1], "email": user[2]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# PUT /users/{user_id} — Update user
# ==========================================

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET name = %s, email = %s
                WHERE id = %s
                RETURNING id, name, email
                """,
                (user.name, user.email, user_id),
            )
            updated_user = cur.fetchone()
        if updated_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "message": "User updated successfully",
            "user": {
                "id": updated_user[0],
                "name": updated_user[1],
                "email": updated_user[2],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# DELETE /users/{user_id} — Delete user
# ==========================================

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                DELETE FROM users
                WHERE id = %s
                RETURNING id, name, email
                """,
                (user_id,),
            )
            deleted_user = cur.fetchone()
        if deleted_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "message": "User deleted successfully",
            "deleted_user": {
                "id": deleted_user[0],
                "name": deleted_user[1],
                "email": deleted_user[2],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# POST /login — Login (access + refresh tokens)
# ==========================================

@app.post("/login")
def login_user(user: LoginRequest):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, password_hash
                FROM users WHERE email = %s
                """,
                (user.email,),
            )
            found_user = cur.fetchone()

        if found_user is None:
            raise HTTPException(401, "Invalid email or password")

        if not verify_password(user.password, found_user[3]):
            raise HTTPException(401, "Invalid email or password")

        # 2 ta token banao
        access_token = create_access_token(found_user[0], expires_minutes=15)
        refresh_token = create_refresh_token(found_user[0])
        refresh_hash = hash_token(refresh_token)

        # DB e refresh hash save
        with get_cursor() as cur:
            cur.execute(
                "UPDATE users SET refresh_token_hash = %s WHERE id = %s",
                (refresh_hash, found_user[0]),
            )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 900,
            "user": {
                "id": found_user[0],
                "name": found_user[1],
                "email": found_user[2],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        raise HTTPException(500, "Login failed")


# ==========================================
# POST /refresh — Get new access token
# ==========================================

@app.post("/refresh")
def refresh_access_token(data: RefreshRequest):
    payload = decode_access_token(data.refresh_token)
    if not payload:
        raise HTTPException(401, "Invalid refresh token")

    user_id = int(payload["sub"])

    with get_cursor() as cur:
        cur.execute(
            "SELECT refresh_token_hash FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()

    if not row or row[0] != hash_token(data.refresh_token):
        raise HTTPException(401, "Refresh token revoked")

    new_access = create_access_token(user_id, expires_minutes=15)

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": 900,
    }


# ==========================================
# POST /logout — Revoke refresh token
# ==========================================

@app.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute(
            "UPDATE users SET refresh_token_hash = NULL WHERE id = %s",
            (current_user["id"],),
        )
    return {"message": "Logged out successfully"}


# ==========================================
# GET /profile — Protected route
# ==========================================

@app.get("/profile")
def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
    }
# ==========================================
# GET /admin/users — Admin only: all users with role
# ==========================================

@app.get("/admin/users")
def admin_get_all_users(admin: dict = Depends(get_current_admin)):
    """Admin-only: get all users with roles"""
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT id, name, email, role FROM users ORDER BY id"
            )
            users = cur.fetchall()
        return [
            {"id": u[0], "name": u[1], "email": u[2], "role": u[3]}
            for u in users
        ]
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==========================================
# DELETE /admin/users/{user_id} — Admin only: delete user
# ==========================================

@app.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    admin: dict = Depends(get_current_admin)
):
    """Admin-only: delete any user"""
    try:
        if user_id == admin["id"]:
            raise HTTPException(400, "Cannot delete yourself")
        
        with get_cursor() as cur:
            cur.execute(
                "DELETE FROM users WHERE id = %s RETURNING id, name, email",
                (user_id,)
            )
            deleted = cur.fetchone()
        
        if deleted is None:
            raise HTTPException(404, "User not found")
        
        return {
            "message": "User deleted by admin",
            "deleted_user": {
                "id": deleted[0],
                "name": deleted[1],
                "email": deleted[2],
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
# ==========================================
# POST /applications — Create
# ==========================================

@app.post("/applications", status_code=201)
def create_application(
    data: ApplicationCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM companies WHERE id = %s", (data.company_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, "Company not found")
        
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO applications 
                    (user_id, company_id, job_role, status, deadline, oa_status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, user_id, company_id, job_role, status, 
                          deadline, oa_status, application_date
                """,
                (current_user["id"], data.company_id, data.job_role,
                 data.status, data.deadline, data.oa_status),
            )
            row = cur.fetchone()
        
        return {
            "id": row[0], "user_id": row[1], "company_id": row[2],
            "job_role": row[3], "status": row[4],
            "deadline": str(row[5]) if row[5] else None,
            "oa_status": row[6],
            "application_date": str(row[7]) if row[7] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
@app.get("/applications/stats", response_model=ApplicationStats)
def get_application_stats(current_user: dict = Depends(get_current_user)):
    """
    Dashboard er jonno statistics:
    Total, Applied, OA, Interview, Offer, Rejected
    """
    try:
        with get_cursor() as cur:
            # Ek query te sob count ber korbo
            cur.execute("""
                SELECT 
                    COUNT(*) AS total,
                    COUNT(CASE WHEN status = 'Applied' THEN 1 END) AS applied,
                    COUNT(CASE WHEN status = 'OA' THEN 1 END) AS oa,
                    COUNT(CASE WHEN status = 'Interview' THEN 1 END) AS interview,
                    COUNT(CASE WHEN status = 'Offer' THEN 1 END) AS offer,
                    COUNT(CASE WHEN status = 'Rejected' THEN 1 END) AS rejected
                FROM applications
                WHERE user_id = %s
            """, (current_user["id"],))
            
            row = cur.fetchone()
            
        return {
            "total_applications": row[0],
            "applied": row[1],
            "oa": row[2],
            "interview": row[3],
            "offer": row[4],
            "rejected": row[5]
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))




# ==========================================
# GET /applications/{id} — Single
# ==========================================
@app.get("/applications")
def get_my_applications(
    status_filter: str | None = Query(None, alias="status"),
    company_id: int | None = None,
    company_name: str | None = None, # <-- Notun filter
    current_user: dict = Depends(get_current_user)
):
    """
    Nijer applications list. Filter: ?status=Applied, ?company_id=1, ?company_name=Google
    """
    try:
        query = """
            SELECT 
                a.id, a.user_id, a.company_id, a.job_role, a.status,
                a.deadline, a.oa_status, a.application_date,
                c.name AS company_name
            FROM applications a
            INNER JOIN companies c ON a.company_id = c.id
            WHERE a.user_id = %s
        """
        params = [current_user["id"]]

        if status_filter:
            query += " AND a.status = %s"
            params.append(status_filter)
            
        if company_id:
            query += " AND a.company_id = %s"
            params.append(company_id)

        if company_name: # <-- Notun Filter logic
            query += " AND c.name ILIKE %s"
            params.append(f"%{company_name}%") # ILIKE mane case-insensitive search

        query += " ORDER BY a.application_date DESC"

        with get_cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        
        return [
            {
                "id": r[0], "user_id": r[1], "company_id": r[2],
                "job_role": r[3], "status": r[4],
                "deadline": str(r[5]) if r[5] else None,
                "oa_status": r[6],
                "application_date": str(r[7]) if r[7] else None,
                "company_name": r[8],
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(500, detail=str(e))
@app.get("/applications/{application_id}")
def get_application(
    application_id: int,
    current_user: dict = Depends(get_current_user),
):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT 
                    a.id, a.user_id, a.company_id, a.job_role, a.status,
                    a.deadline, a.oa_status, a.application_date,
                    c.name AS company_name
                FROM applications a
                INNER JOIN companies c ON a.company_id = c.id
                WHERE a.id = %s AND a.user_id = %s
                """,
                (application_id, current_user["id"]),
            )
            row = cur.fetchone()
        
        if row is None:
            raise HTTPException(404, "Application not found")
        
        return {
            "id": row[0], "user_id": row[1], "company_id": row[2],
            "job_role": row[3], "status": row[4],
            "deadline": str(row[5]) if row[5] else None,
            "oa_status": row[6],
            "application_date": str(row[7]) if row[7] else None,
            "company_name": row[8],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))




# ==========================================
# PUT /applications/{id} — Update
# ==========================================

@app.put("/applications/{application_id}")
def update_application(
    application_id: int,
    data: ApplicationUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        updates = []
        values = []
        
        if data.job_role is not None:
            updates.append("job_role = %s")
            values.append(data.job_role)
        if data.status is not None:
            updates.append("status = %s")
            values.append(data.status)
        if data.deadline is not None:
            updates.append("deadline = %s")
            values.append(data.deadline)
        if data.oa_status is not None:
            updates.append("oa_status = %s")
            values.append(data.oa_status)
        
        if not updates:
            raise HTTPException(400, "No fields to update")
        
        values.extend([application_id, current_user["id"]])
        query = f"""
            UPDATE applications
            SET {', '.join(updates)}
            WHERE id = %s AND user_id = %s
            RETURNING id, user_id, company_id, job_role, status, 
                      deadline, oa_status, application_date
        """
        
        with get_cursor() as cur:
            cur.execute(query, values)
            row = cur.fetchone()
        
        if row is None:
            raise HTTPException(404, "Application not found")
        
        return {
            "id": row[0], "user_id": row[1], "company_id": row[2],
            "job_role": row[3], "status": row[4],
            "deadline": str(row[5]) if row[5] else None,
            "oa_status": row[6],
            "application_date": str(row[7]) if row[7] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==========================================
# DELETE /applications/{id}
# ==========================================

@app.delete("/applications/{application_id}", status_code=204)
def delete_application(
    application_id: int,
    current_user: dict = Depends(get_current_user),
):
    try:
        with get_cursor() as cur:
            cur.execute(
                "DELETE FROM applications WHERE id = %s AND user_id = %s RETURNING id",
                (application_id, current_user["id"]),
            )
            deleted = cur.fetchone()
        
        if deleted is None:
            raise HTTPException(404, "Application not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
# ==========================================
# GET /applications/stats — Dashboard Stats
# ==========================================
# ==========================================
# POST /companies — Admin Only (Create)
# ==========================================

@app.post("/companies", response_model=CompanyResponse, status_code=201)
def create_company(
    data: CompanyCreate,
    admin: dict = Depends(get_current_admin)  # Admin check
):
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO companies (name, location, website)
                VALUES (%s, %s, %s)
                RETURNING id, name, location, website
                """,
                (data.name, data.location, data.website),
            )
            row = cur.fetchone()
        
        return {
            "id": row[0], "name": row[1], 
            "location": row[2], "website": row[3]
        }
    except Exception as e:
        # Unique violation handling (jodi same naam er company thake)
        if "unique constraint" in str(e).lower():
            raise HTTPException(400, "Company already exists")
        raise HTTPException(500, detail=str(e))


# ==========================================
# GET /companies — List (Sob user dekhte parbe)
# ==========================================

@app.get("/companies")
def get_companies(current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, location, website FROM companies ORDER BY name")
            rows = cur.fetchall()
        
        return [
            {"id": r[0], "name": r[1], "location": r[2], "website": r[3]}
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==========================================
# GET /companies/{id} — Single Company
# ==========================================

@app.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT id, name, location, website FROM companies WHERE id = %s",
                (company_id,),
            )
            row = cur.fetchone()
        
        if row is None:
            raise HTTPException(404, "Company not found")
        
        return {
            "id": row[0], "name": row[1], 
            "location": row[2], "website": row[3]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==========================================
# DELETE /companies/{id} — Admin Only
# ==========================================

@app.delete("/companies/{company_id}", status_code=204)
def delete_company(company_id: int, admin: dict = Depends(get_current_admin)):
    try:
        with get_cursor() as cur:
            cur.execute(
                "DELETE FROM companies WHERE id = %s RETURNING id",
                (company_id,),
            )
            deleted = cur.fetchone()
        
        if deleted is None:
            raise HTTPException(404, "Company not found")
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
# ==========================================
# POST /applications/{id}/interviews — Add Interview
# ==========================================

@app.post("/applications/{application_id}/interviews", status_code=201)
def add_interview(
    application_id: int,
    data: InterviewCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        # Step 1: Check koro application ta user er ki na
        with get_cursor() as cur:
            cur.execute(
                "SELECT id FROM applications WHERE id = %s AND user_id = %s",
                (application_id, current_user["id"]),
            )
            if cur.fetchone() is None:
                raise HTTPException(404, "Application not found")

        # Step 2: Interview insert koro
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO interviews 
                    (application_id, interview_type, interview_date, status, result, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, application_id, interview_type, interview_date, status, result, notes
                """,
                (
                    application_id, data.interview_type, data.interview_date,
                    data.status, data.result, data.notes
                ),
            )
            row = cur.fetchone()

        return {
            "id": row[0], "application_id": row[1],
            "interview_type": row[2],
            "interview_date": str(row[3]) if row[3] else None,
            "status": row[4], "result": row[5], "notes": row[6],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
# ==========================================
# GET /applications/{id}/interviews — List
# ==========================================

@app.get("/applications/{application_id}/interviews")
def get_interviews(
    application_id: int,
    current_user: dict = Depends(get_current_user),
):
    try:
        # Check application ownership
        with get_cursor() as cur:
            cur.execute(
                "SELECT id FROM applications WHERE id = %s AND user_id = %s",
                (application_id, current_user["id"]),
            )
            if cur.fetchone() is None:
                raise HTTPException(404, "Application not found")

        # Fetch interviews
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT id, application_id, interview_type, interview_date, status, result, notes
                FROM interviews
                WHERE application_id = %s
                ORDER BY id
                """,
                (application_id,),
            )
            rows = cur.fetchall()

        return [
            {
                "id": r[0], "application_id": r[1],
                "interview_type": r[2],
                "interview_date": str(r[3]) if r[3] else None,
                "status": r[4], "result": r[5], "notes": r[6],
            }
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
# ==========================================
# PUT /interviews/{id} — Update Interview
# ==========================================

@app.put("/interviews/{interview_id}")
def update_interview(
    interview_id: int,
    data: InterviewUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        # Check ownership (interview -> application -> user)
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT i.id FROM interviews i
                INNER JOIN applications a ON i.application_id = a.id
                WHERE i.id = %s AND a.user_id = %s
                """,
                (interview_id, current_user["id"]),
            )
            if cur.fetchone() is None:
                raise HTTPException(404, "Interview not found")

        # Dynamic Update
        updates = []
        values = []
        if data.interview_date is not None:
            updates.append("interview_date = %s")
            values.append(data.interview_date)
        if data.status is not None:
            updates.append("status = %s")
            values.append(data.status)
        if data.result is not None:
            updates.append("result = %s")
            values.append(data.result)
        if data.notes is not None:
            updates.append("notes = %s")
            values.append(data.notes)

        if not updates:
            raise HTTPException(400, "No fields to update")

        values.append(interview_id)
        query = f"""
            UPDATE interviews SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, application_id, interview_type, interview_date, status, result, notes
        """

        with get_cursor() as cur:
            cur.execute(query, values)
            row = cur.fetchone()

        return {
            "id": row[0], "application_id": row[1],
            "interview_type": row[2],
            "interview_date": str(row[3]) if row[3] else None,
            "status": row[4], "result": row[5], "notes": row[6],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))
# ==========================================
# GET /dashboard/user — User's Unified Stats
# ==========================================

@app.get("/dashboard/user", response_model=UserDashboardStats)
def get_user_dashboard(current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            # Application ar Interview count ek sathe
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM applications WHERE user_id = %s) AS total_apps,
                    (SELECT COUNT(*) FROM interviews i 
                     INNER JOIN applications a ON i.application_id = a.id 
                     WHERE a.user_id = %s AND i.status = 'Scheduled') AS interviews,
                    (SELECT COUNT(*) FROM applications WHERE user_id = %s AND status = 'Offer') AS offers,
                    (SELECT COUNT(*) FROM applications WHERE user_id = %s AND status = 'Rejected') AS rejections
            """, (current_user["id"], current_user["id"], current_user["id"], current_user["id"]))
            
            row = cur.fetchone()
            
        return {
            "total_applications": row[0],
            "interview_scheduled": row[1],
            "offers_received": row[2],
            "rejections": row[3]
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))
# ==========================================
# GET /dashboard/admin — System-wide Stats
# ==========================================

@app.get("/dashboard/admin", response_model=AdminDashboardStats)
def get_admin_dashboard(admin: dict = Depends(get_current_admin)):
    try:
        with get_cursor() as cur:
            # Puro system er count (Admin only)
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users) AS users,
                    (SELECT COUNT(*) FROM companies) AS companies,
                    (SELECT COUNT(*) FROM applications) AS apps,
                    (SELECT COUNT(*) FROM interviews) AS interviews
            """)
            
            row = cur.fetchone()
            
        return {
            "total_users": row[0],
            "total_companies": row[1],
            "total_applications": row[2],
            "total_interviews": row[3]
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


