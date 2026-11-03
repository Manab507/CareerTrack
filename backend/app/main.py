from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Routers import koro
from .routers import auth, users, apps, dashboard
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .limiter import limiter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CareerTrack API",
    description="Placement and Internship Tracker Backend",
    version="1.0.0"
)
# ==========================================
# CORS Setup
# ==========================================
origins = [
    "http://localhost:3000",    # React (Vite/CRA)
    "http://localhost:5173",    # Vite default port
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # pore production e tomar live domain ekhane add korbe
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Kon kon URL theke ashte parbe
    allow_credentials=True,      # Cookies/Token pathate parbe
    allow_methods=["*"],         # GET, POST, PUT, DELETE sob allow
    allow_headers=["*"],         # Sob header allow
)

# Rate Limiter Setup
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