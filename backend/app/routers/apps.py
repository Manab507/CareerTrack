from fastapi import APIRouter, HTTPException, Depends, Query,Request
from ..database import get_cursor
from ..schemas import (
    ApplicationCreate, ApplicationUpdate, CompanyCreate, CompanyResponse, 
    InterviewCreate, InterviewUpdate
)
from ..dependencies import get_current_user, get_current_admin
from ..limiter import limiter

router = APIRouter(tags=["Applications, Companies & Interviews"])

# ==========================================
# APPLICATIONS
# ==========================================

@router.post("/")
@limiter.limit("10/minute") # 1 minute e max 10 ta application
def create_application(request: Request, data: ApplicationCreate, current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM companies WHERE id = %s", (data.company_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, "Company not found")
        with get_cursor() as cur:
            cur.execute(
                "INSERT INTO applications (user_id, company_id, job_role, status, deadline, oa_status) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, user_id, company_id, job_role, status, deadline, oa_status, application_date",
                (current_user["id"], data.company_id, data.job_role, data.status, data.deadline, data.oa_status),
            )
            row = cur.fetchone()
        return {"id": row[0], "user_id": row[1], "company_id": row[2], "job_role": row[3], "status": row[4], "deadline": str(row[5]) if row[5] else None, "oa_status": row[6], "application_date": str(row[7]) if row[7] else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.get("/applications")
def get_my_applications(
    status_filter: str | None = Query(None, alias="status"),
    company_id: int | None = None,
    company_name: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        query = "SELECT a.id, a.user_id, a.company_id, a.job_role, a.status, a.deadline, a.oa_status, a.application_date, c.name AS company_name FROM applications a INNER JOIN companies c ON a.company_id = c.id WHERE a.user_id = %s"
        params = [current_user["id"]]
        if status_filter:
            query += " AND a.status = %s"
            params.append(status_filter)
        if company_id:
            query += " AND a.company_id = %s"
            params.append(company_id)
        if company_name:
            query += " AND c.name ILIKE %s"
            params.append(f"%{company_name}%")
        query += " ORDER BY a.application_date DESC"
        with get_cursor() as cur:
            cur.execute(query, tuple(params))
            rows = cur.fetchall()
        return [{"id": r[0], "user_id": r[1], "company_id": r[2], "job_role": r[3], "status": r[4], "deadline": str(r[5]) if r[5] else None, "oa_status": r[6], "application_date": str(r[7]) if r[7] else None, "company_name": r[8]} for r in rows]
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.get("/applications/{application_id}")
def get_application(application_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT a.id, a.user_id, a.company_id, a.job_role, a.status, a.deadline, a.oa_status, a.application_date, c.name AS company_name FROM applications a INNER JOIN companies c ON a.company_id = c.id WHERE a.id = %s AND a.user_id = %s", (application_id, current_user["id"]))
            row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Application not found")
        return {"id": row[0], "user_id": row[1], "company_id": row[2], "job_role": row[3], "status": row[4], "deadline": str(row[5]) if row[5] else None, "oa_status": row[6], "application_date": str(row[7]) if row[7] else None, "company_name": row[8]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.put("/applications/{application_id}")
def update_application(application_id: int, data: ApplicationUpdate, current_user: dict = Depends(get_current_user)):
    try:
        updates = []
        values = []
        if data.job_role is not None:
            updates.append("job_role = %s"); values.append(data.job_role)
        if data.status is not None:
            updates.append("status = %s"); values.append(data.status)
        if data.deadline is not None:
            updates.append("deadline = %s"); values.append(data.deadline)
        if data.oa_status is not None:
            updates.append("oa_status = %s"); values.append(data.oa_status)
        if not updates:
            raise HTTPException(400, "No fields to update")
        values.extend([application_id, current_user["id"]])
        query = f"UPDATE applications SET {', '.join(updates)} WHERE id = %s AND user_id = %s RETURNING id, user_id, company_id, job_role, status, deadline, oa_status, application_date"
        with get_cursor() as cur:
            cur.execute(query, values)
            row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Application not found")
        return {"id": row[0], "user_id": row[1], "company_id": row[2], "job_role": row[3], "status": row[4], "deadline": str(row[5]) if row[5] else None, "oa_status": row[6], "application_date": str(row[7]) if row[7] else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.delete("/applications/{application_id}", status_code=204)
def delete_application(application_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("DELETE FROM applications WHERE id = %s AND user_id = %s RETURNING id", (application_id, current_user["id"]))
            deleted = cur.fetchone()
        if deleted is None:
            raise HTTPException(404, "Application not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==========================================
# COMPANIES
# ==========================================

@router.post("/companies", response_model=CompanyResponse, status_code=201)
def create_company(data: CompanyCreate, admin: dict = Depends(get_current_admin)):
    try:
        with get_cursor() as cur:
            cur.execute("INSERT INTO companies (name, location, website) VALUES (%s, %s, %s) RETURNING id, name, location, website", (data.name, data.location, data.website))
            row = cur.fetchone()
        return {"id": row[0], "name": row[1], "location": row[2], "website": row[3]}
    except Exception as e:
        if "unique constraint" in str(e).lower():
            raise HTTPException(400, "Company already exists")
        raise HTTPException(500, detail=str(e))

@router.get("/companies")
def get_companies(current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, location, website FROM companies ORDER BY name")
            rows = cur.fetchall()
        return [{"id": r[0], "name": r[1], "location": r[2], "website": r[3]} for r in rows]
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.get("/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id, name, location, website FROM companies WHERE id = %s", (company_id,))
            row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Company not found")
        return {"id": row[0], "name": row[1], "location": row[2], "website": row[3]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.delete("/companies/{company_id}", status_code=204)
def delete_company(company_id: int, admin: dict = Depends(get_current_admin)):
    try:
        with get_cursor() as cur:
            cur.execute("DELETE FROM companies WHERE id = %s RETURNING id", (company_id,))
            deleted = cur.fetchone()
        if deleted is None:
            raise HTTPException(404, "Company not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ==========================================
# INTERVIEWS
# ==========================================

@router.post("/applications/{application_id}/interviews", status_code=201)
def add_interview(application_id: int, data: InterviewCreate, current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM applications WHERE id = %s AND user_id = %s", (application_id, current_user["id"]))
            if cur.fetchone() is None:
                raise HTTPException(404, "Application not found")
        with get_cursor() as cur:
            cur.execute("INSERT INTO interviews (application_id, interview_type, interview_date, status, result, notes) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, application_id, interview_type, interview_date, status, result, notes", (application_id, data.interview_type, data.interview_date, data.status, data.result, data.notes))
            row = cur.fetchone()
        return {"id": row[0], "application_id": row[1], "interview_type": row[2], "interview_date": str(row[3]) if row[3] else None, "status": row[4], "result": row[5], "notes": row[6]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.get("/applications/{application_id}/interviews")
def get_interviews(application_id: int, current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT id FROM applications WHERE id = %s AND user_id = %s", (application_id, current_user["id"]))
            if cur.fetchone() is None:
                raise HTTPException(404, "Application not found")
        with get_cursor() as cur:
            cur.execute("SELECT id, application_id, interview_type, interview_date, status, result, notes FROM interviews WHERE application_id = %s ORDER BY id", (application_id,))
            rows = cur.fetchall()
        return [{"id": r[0], "application_id": r[1], "interview_type": r[2], "interview_date": str(r[3]) if r[3] else None, "status": r[4], "result": r[5], "notes": r[6]} for r in rows]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.put("/interviews/{interview_id}")
def update_interview(interview_id: int, data: InterviewUpdate, current_user: dict = Depends(get_current_user)):
    try:
        with get_cursor() as cur:
            cur.execute("SELECT i.id FROM interviews i INNER JOIN applications a ON i.application_id = a.id WHERE i.id = %s AND a.user_id = %s", (interview_id, current_user["id"]))
            if cur.fetchone() is None:
                raise HTTPException(404, "Interview not found")
        updates = []
        values = []
        if data.interview_date is not None:
            updates.append("interview_date = %s"); values.append(data.interview_date)
        if data.status is not None:
            updates.append("status = %s"); values.append(data.status)
        if data.result is not None:
            updates.append("result = %s"); values.append(data.result)
        if data.notes is not None:
            updates.append("notes = %s"); values.append(data.notes)
        if not updates:
            raise HTTPException(400, "No fields to update")
        values.append(interview_id)
        query = f"UPDATE interviews SET {', '.join(updates)} WHERE id = %s RETURNING id, application_id, interview_type, interview_date, status, result, notes"
        with get_cursor() as cur:
            cur.execute(query, values)
            row = cur.fetchone()
        return {"id": row[0], "application_id": row[1], "interview_type": row[2], "interview_date": str(row[3]) if row[3] else None, "status": row[4], "result": row[5], "notes": row[6]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))