from fastapi import FastAPI, Request, Response, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import openai
import sentry_sdk
from loguru import logger
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Sentry
sentry_dsn = os.getenv('SENTRY_DSN')
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

# Validate OpenAI key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found")
openai.api_key = api_key

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
if not supabase_url or not supabase_key:
    raise ValueError("Supabase credentials not found")
supabase: Client = create_client(supabase_url, supabase_key)

# Create FastAPI app
app = FastAPI(title="Resume Optimizer API")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://resumegen-ai.vercel.app",
    os.getenv('FRONTEND_URL'),
    os.getenv('FRONTEND_URL_DEV'),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routes.optimize_routes import router as optimize_router
from routes.job_routes import router as jobs_router
from routes.resume_routes import router as resumes_router
from routes.user_routes import router as users_router
from routes.scrape_routes import router as scrape_router
from routes.subscription_routes import router as subscriptions_router

# Include routers
app.include_router(optimize_router)
app.include_router(jobs_router)
app.include_router(resumes_router)
app.include_router(users_router)
app.include_router(scrape_router)
app.include_router(subscriptions_router)

@app.get("/")
async def root():
    return {"message": "Resume Optimizer API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)