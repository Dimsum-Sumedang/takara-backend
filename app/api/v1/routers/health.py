from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Agents API",
        "mode": "async-first"
    }