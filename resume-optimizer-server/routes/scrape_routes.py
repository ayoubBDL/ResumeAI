from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from services.linkedin_batch_scraper import LinkedInJobScraper

app = FastAPI()

class ScrapeJobsRequest(BaseModel):
    search_queries: list
    max_jobs: int = 25

class ScrapeJobUrlRequest(BaseModel):
    job_url: str

router = APIRouter(tags=["scrape-jobs"])

@app.post("/scrape-jobs")
async def scrape_jobs(request: ScrapeJobsRequest):
    """Endpoint to scrape jobs from LinkedIn based on search criteria"""
    try:
        scraper = LinkedInJobScraper()
        jobs = scraper.scrape_jobs(request.search_queries, request.max_jobs)

        return {
            "success": True,
            "data": {
                "jobs": jobs,
                "count": len(jobs)
            }
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape-job-url")
async def scrape_job_url(request: ScrapeJobUrlRequest):
    """Endpoint to scrape a job from a specific LinkedIn URL"""
    try:
        scraper = LinkedInJobScraper()
        job_details = scraper.scrape_job_by_url(request.job_url)

        if job_details is None:
            raise HTTPException(status_code=404, detail="Failed to scrape job details")

        return {
            "success": True,
            "data": job_details
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
