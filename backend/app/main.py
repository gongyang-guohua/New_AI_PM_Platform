# backend/app/main.py
from fastapi import FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.agent_chat import router as agent_router

app = FastAPI(
    title="ProjectMaster AI Platform",
    description="Engineering-grade AI project management API",
    version="1.0.0",
)

# CORS Security
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Should be tightened in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registries
app.include_router(agent_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to ProjectMaster AI Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
