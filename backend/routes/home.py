from fastapi import APIRouter

router = APIRouter()

@router.get("/home")
async def home():
    return {"message": "Hello World"}


@router.get("/api/home")
async def api_home():
    return await home()