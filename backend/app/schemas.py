"""
CareerTrack — Pydantic Schemas
Request/Response validation models
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime


# ==========================================
# User Schemas
# ==========================================

class UserBase(BaseModel):
    """Base user fields"""
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """POST /users"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """PUT /users/{id}"""
    name: str | None = Field(None, min_length=2, max_length=50)
    email: EmailStr | None = None


class UserResponse(UserBase):
    """User response"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime | None = None


# ==========================================
# Auth Schemas
# ==========================================

class LoginRequest(BaseModel):
    """POST /login"""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """POST /refresh"""
    refresh_token: str


# ==========================================
# Application Schemas
# ==========================================

class ApplicationCreate(BaseModel):
    """POST /applications"""
    company_id: int
    job_role: str = Field(..., min_length=2, max_length=100)
    status: str = Field("Applied", max_length=30)
    deadline: str | None = None
    oa_status: str = Field("Not Required", max_length=30)


class ApplicationUpdate(BaseModel):
    """PUT /applications/{id}"""
    job_role: str | None = Field(None, min_length=2, max_length=100)
    status: str | None = Field(None, max_length=30)
    deadline: str | None = None
    oa_status: str | None = Field(None, max_length=30)


class ApplicationResponse(BaseModel):
    """Application response"""
    id: int
    user_id: int
    company_id: int
    job_role: str
    status: str
    deadline: str | None = None
    oa_status: str | None = None
    application_date: str | None = None
# ==========================================
# Dashboard Schemas
# ==========================================

class ApplicationStats(BaseModel):
    total_applications: int
    applied: int
    oa: int
    interview: int
    offer: int
    rejected: int
# ==========================================
# Company Schemas
# ==========================================

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    location: str | None = Field(None, max_length=100)
    website: str | None = Field(None, max_length=255)


class CompanyResponse(BaseModel):
    id: int
    name: str
    location: str | None = None
    website: str | None = None
# ==========================================
# Interview Schemas
# ==========================================

class InterviewCreate(BaseModel):
    interview_type: str = Field(..., max_length=50)
    interview_date: str | None = None
    status: str = Field("Scheduled", max_length=30)
    result: str = Field("Pending", max_length=30)
    notes: str | None = None


class InterviewUpdate(BaseModel):
    interview_date: str | None = None
    status: str | None = Field(None, max_length=30)
    result: str | None = Field(None, max_length=30)
    notes: str | None = None


class InterviewResponse(BaseModel):
    id: int
    application_id: int
    interview_type: str
    interview_date: str | None = None
    status: str
    result: str
    notes: str | None = None
# ==========================================
# Dashboard Schemas (Day 59)
# ==========================================

class UserDashboardStats(BaseModel):
    total_applications: int
    interview_scheduled: int
    offers_received: int
    rejections: int


class AdminDashboardStats(BaseModel):
    total_users: int
    total_companies: int
    total_applications: int
    total_interviews: int