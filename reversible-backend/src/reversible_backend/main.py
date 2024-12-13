from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from ..routes import auth, transactions, disputes, users, judges

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(disputes.router)
app.include_router(users.router)
app.include_router(judges.router)

@app.get("/health")
async def root():
    return {"status": "healthy"}