from fastapi import APIRouter
from app.api.v1.endpoints import auth, uploads, startups, analysis, memos, exports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(uploads.router, prefix="/upload", tags=["upload"])
api_router.include_router(startups.router, prefix="/startups", tags=["startups"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(memos.router, prefix="/memos", tags=["memos"])
api_router.include_router(exports.router, prefix="/export", tags=["export"])
