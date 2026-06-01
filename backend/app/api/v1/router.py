from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, interviews, jd, resume

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(resume.router, prefix="/resume", tags=["Resume"])
api_router.include_router(jd.router, prefix="/jd", tags=["Job Description"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])
