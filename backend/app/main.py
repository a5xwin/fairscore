from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes.auth import router as auth_router
from app.routes.borrower import router as borrower_router
from app.routes.lender import router as lender_router

load_dotenv()

app = FastAPI(title="FairScore Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(borrower_router, prefix="/borrower")
app.include_router(lender_router, prefix="/lender")

@app.get("/health")
def health():
    return {"status": "ok"}