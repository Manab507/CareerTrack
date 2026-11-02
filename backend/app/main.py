from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Routers import koro
from .routers import auth, users, apps, dashboard
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

app = FastAPI(
    title="CareerTrack API",
    description="Placement and Internship Tracker Backend",
    version="1.0.0"
)
# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ==========================================
# Global Exception Handler
# ==========================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"❌ Global Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error. Amra eta fix korchi!",
            "detail": str(exc)
        }
    )

# ==========================================
# Routers Connect Koro
# ==========================================
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(apps.router)
app.include_router(dashboard.router)

# ==========================================
# Root Endpoint
# ==========================================
@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to CareerTrack API 🚀"}