from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

app = FastAPI(title="Codebase Intelligence API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Codebase Intelligence API"}

# Include API routes
app.include_router(api_router, prefix="/api", tags=["api"])
