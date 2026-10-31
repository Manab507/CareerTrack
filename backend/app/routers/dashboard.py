from fastapi import APIRouter, Depends, HTTPException
from ..database import get_cursor
from ..schemas import ApplicationStats, UserDashboardStats, AdminDashboardStats
from ..dependencies import get_current_user, get_current_admin

router = APIRouter(tags=["Dashboard"])

# ==========================================
# GET /dashboard/user — User's Unified Stats
# ==========================================
@router.get("/dashboard/user", response_model=UserDashboardStats)
def get_user_dashboard(current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM applications WHERE user_id = %s),
                    (SELECT COUNT(*) FROM interviews i INNER JOIN applications a ON i.application_id = a.id WHERE a.user_id = %s AND i.status = 'Scheduled'),
                    (SELECT COUNT(*) FROM applications WHERE user_id = %s AND status = 'Offer'),
                    (SELECT COUNT(*) FROM applications WHERE user_id = %s AND status = 'Rejected')
            """, (current_user["id"], current_user["id"], current_user["id"], current_user["id"]))
            row = cur.fetchone()
        return {"total_applications": row[0], "interview_scheduled": row[1], "offers_received": row[2], "rejections": row[3]}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==========================================
# GET /dashboard/admin — System-wide Stats
# ==========================================
@router.get("/dashboard/admin", response_model=AdminDashboardStats)
def get_admin_dashboard(admin: dict = Depends(get_current_admin)):
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users),
                    (SELECT COUNT(*) FROM companies),
                    (SELECT COUNT(*) FROM applications),
                    (SELECT COUNT(*) FROM interviews)
            """)
            row = cur.fetchone()
        return {"total_users": row[0], "total_companies": row[1], "total_applications": row[2], "total_interviews": row[3]}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==========================================
# GET /applications/stats — Application Stats
# ==========================================
@router.get("/applications/stats", response_model=ApplicationStats)
def get_application_stats(current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*), 
                    COUNT(CASE WHEN status = 'Applied' THEN 1 END),
                    COUNT(CASE WHEN status = 'OA' THEN 1 END),
                    COUNT(CASE WHEN status = 'Interview' THEN 1 END),
                    COUNT(CASE WHEN status = 'Offer' THEN 1 END),
                    COUNT(CASE WHEN status = 'Rejected' THEN 1 END)
                FROM applications WHERE user_id = %s
            """, (current_user["id"],))
            row = cur.fetchone()
        return {"total_applications": row[0], "applied": row[1], "oa": row[2], "interview": row[3], "offer": row[4], "rejected": row[5]}
    except Exception as e:
        raise HTTPException(500, detail=str(e))