from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Optional, List
import os
from pydantic import BaseModel
from datetime import datetime
from supabase import create_client, Client
from services.linkedin_scraper import LinkedInJobScraper

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

router = APIRouter(tags=["jobs"])
supabase: Client = create_client(supabase_url, supabase_key)

# Pydantic models for request/response validation
class JobBase(BaseModel):
    job_title: str
    company: str
    job_description: str
    job_url: str

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    status: str

class JobResponse(JobBase):
    id: str
    user_id: str
    resume_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    analysis: Optional[dict]
    resume_title: Optional[str]

    class Config:
        arbitrary_types_allowed = True

@router.get("/job/{job_id}")
def get_job(
    job_id: str,
    x_user_id: str = Header(..., alias="X-User-Id")
):
    try:
        
        response =  supabase.table('job_applications')\
            .select('*, resume:resumes(id, analysis, title, created_at)')\
            .eq('id', job_id)\
            .eq('user_id', x_user_id)\
            .single()\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Job not found or not authorized")

        job_data = {**response.data}
        if job_data.get('resume'):
            job_data['analysis'] = job_data['resume'].get('analysis')

        return {"success": True, "data": job_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/jobs")
def get_jobs(x_user_id: str = Header(..., alias="X-User-Id")):
    try:
        response = supabase.table('job_applications')\
            .select('*, resume:resumes(id, analysis, title, created_at, optimized_pdf_url)')\
            .eq('user_id', x_user_id)\
            .order('created_at', desc=True)\
            .execute()

        if not response.data:
            return []

        jobs = []
        for job in response.data:
            job_data = {**job}
            if job.get('resume'):
                resume = job['resume']
                job_data['analysis'] = resume.get('analysis')
                job_data['resume_title'] = resume.get('title')
                job_data['resume_id'] = resume.get('id')
            jobs.append(job_data)

        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/jobs")
def create_job(
    job: JobCreate,
    x_user_id: str = Header(..., alias="X-User-Id")
):
    try:
        # Get latest resume
        resume_response = supabase.table('resumes')\
            .select('id')\
            .eq('user_id', x_user_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()

        resume_id = resume_response.data[0]['id'] if resume_response.data else None

        job_data = {
            'user_id': x_user_id,
            'resume_id': resume_id,
            'company': job.company,
            'job_title': job.job_title,
            'job_url': job.job_url,
            'job_description': job.job_description,
            'status': 'new',
            'created_at': 'now()',
            'updated_at': 'now()'
        }

        response = supabase.table('job_applications')\
            .insert(job_data)\
            .execute()

        return {"success": True, "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/jobs/{job_id}/download")
def download_job_resume(
    job_id: str,
    x_user_id: str = Header(..., alias="X-User-Id")
):
    try:
        response =  supabase.table('job_applications')\
            .select('resume:resumes(optimized_pdf_url)')\
            .eq('id', job_id)\
            .eq('user_id', x_user_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Resume not found or not authorized")

        optimized_pdf_url = response.data[0]['resume'].get('optimized_pdf_url')
        if not optimized_pdf_url:
            raise HTTPException(status_code=404, detail="Resume file not found")

        file_path = optimized_pdf_url.split('/resumes/')[1].split('?')[0]
        signed_url_response =  supabase.storage\
            .from_('resumes')\
            .create_signed_url(file_path, 300)

        if not signed_url_response or 'signedURL' not in signed_url_response:
            raise HTTPException(status_code=500, detail="Failed to generate download URL")

        return {"success": True, "url": signed_url_response['signedURL']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/jobs/{job_id}/status")
def update_job_status(
    job_id: str,
    job_update: JobUpdate,
    x_user_id: str = Header(..., alias="X-User-Id")
):
    valid_statuses = ['new', 'applied', 'interviewing', 'offered', 'rejected']
    if job_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )

    try:
        response =  supabase.table('job_applications')\
            .update({'status': job_update.status, 'updated_at': 'now()'})\
            .eq('id', job_id)\
            .eq('user_id', x_user_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Job not found or not authorized")

        return {"success": True, "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/jobs/{job_id}")
def delete_job(
    job_id: str,
    x_user_id: str = Header(..., alias="X-User-Id")
):
    try:
        
        response =  supabase.table('job_applications')\
            .delete()\
            .eq('id', job_id)\
            .eq('user_id', x_user_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Job application not found or unauthorized")

        return {"success": True, "message": "Job application deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class JobSearchQuery(BaseModel):
    job_url: str
    max_jobs: Optional[int] = 25

@router.post("/search-similar-jobs")
def search_similar_jobs(query: JobSearchQuery):
    try:
        scraper = LinkedInJobScraper()
        similar_jobs =  scraper.search_similar_jobs(query.job_url, query.max_jobs)
        return {
            "success": True,
            "data": {
                "jobs": similar_jobs,
                "count": len(similar_jobs)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/get-job-details")
def get_job_details(query: JobSearchQuery):
    try:
        scraper = LinkedInJobScraper()
        job_details =  scraper.get_job_details(query.job_url)
        
        if job_details is None:
            raise HTTPException(status_code=404, detail="Failed to get job details")

        return {"success": True, "data": job_details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))