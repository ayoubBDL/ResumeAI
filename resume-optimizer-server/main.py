from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from services.linkedin_scraper import LinkedInScraper
from services.resume_parser import ResumeParser
from services.resume_optimizer import ResumeOptimizer
from services.pdf_generator import PDFGenerator
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptimizeRequest(BaseModel):
    linkedin_url: str
    custom_instructions: Optional[str] = None

@app.post("/api/optimize-resume")
async def optimize_resume(
    request: OptimizeRequest,
    resume_file: UploadFile = File(...)
):
    try:
        # 1. Scrape LinkedIn job description
        scraper = LinkedInScraper()
        job_data = await scraper.scrape_job(request.linkedin_url)

        # 2. Parse uploaded resume
        resume_parser = ResumeParser()
        resume_text = await resume_parser.parse(resume_file)

        # 3. Optimize resume using AI
        optimizer = ResumeOptimizer()
        optimized_content = await optimizer.optimize(
            resume_text=resume_text,
            job_description=job_data["description"],
            job_title=job_data["title"],
            company=job_data["company"],
            custom_instructions=request.custom_instructions
        )

        # 4. Generate ATS-friendly PDF
        pdf_generator = PDFGenerator()
        pdf_path = await pdf_generator.generate(optimized_content)

        return {
            "status": "success",
            "pdf_url": f"/downloads/{os.path.basename(pdf_path)}",
            "summary": optimized_content["summary"],
            "changes": optimized_content["changes"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
