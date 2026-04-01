import lightgbm
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load .env from the backend/ directory (one level up from app/)
if not load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")):
    print("Warning: .env file not found. Make sure to create one with the necessary environment variables.")
    

from app.routes.auth import router as auth_router
from app.routes.borrower import router as borrower_router
from app.routes.lender import router as lender_router

app = FastAPI(title="FairScore Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routes live under /api/v1 to match the frontend base URL
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(borrower_router)
api_router.include_router(lender_router)

app.include_router(api_router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)