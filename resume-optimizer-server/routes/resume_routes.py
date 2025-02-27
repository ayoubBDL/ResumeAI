from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from services.supabase_client import supabase
from services.pdf_generator import PDFGenerator
from loguru import logger
from io import BytesIO
from dotenv import load_dotenv

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)
load_dotenv()

router = APIRouter()

@router.get("/api/test-pdf")
async def test_pdf():
    try:
        test_content = "Test Resume\n\nSection 1\nThis is a test."
        pdf_generator = PDFGenerator()
        pdf_data = pdf_generator.create_pdf_from_text(test_content)
        
        return StreamingResponse(BytesIO(pdf_data), media_type="application/pdf", headers={
            "Content-Disposition": 'attachment; filename="test.pdf"'
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/resumes/{resume_id}/cover-letter/download")
async def download_cover_letter(resume_id: str, request: Request):
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header")

        response = supabase.table('resumes')\
            .select('cover_letter, title')\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Resume not found or not authorized")

        cover_letter = response.data[0].get('cover_letter')
        if not cover_letter:
            raise HTTPException(status_code=404, detail="Cover letter not found")

        pdf_generator = PDFGenerator()
        pdf_data = pdf_generator.create_cover_letter_pdf(cover_letter)

        filename = f"cover_letter_{response.data[0].get('title', 'document')}"
        return StreamingResponse(BytesIO(pdf_data), media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="{filename}.pdf"'
        })
    except Exception as e:
        logger.error(f"Error generating cover letter PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/resumes")
async def get_resumes(request: Request, limit: int = None):
    try:
        print("Getting resumes")
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header")

        query = supabase.table('resumes')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)
            
        if limit:
            query = query.limit(limit)

        response = query.execute()

        if not response.data:
            return JSONResponse(content=[])

        return JSONResponse(content=response.data)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/resumes/{resume_id}/download")
async def download_resume(resume_id: str, request: Request):
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header")

        response = supabase.table('resumes')\
            .select('content, title')\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Resume not found or not authorized")

        resume_content = response.data[0].get('content')
        if not resume_content:
            raise HTTPException(status_code=404, detail="Resume content not found")

        pdf_generator = PDFGenerator()
        pdf_data = pdf_generator.create_pdf_from_text(resume_content)

        filename = f"resume_{response.data[0].get('title', 'document')}"
        return StreamingResponse(BytesIO(pdf_data), media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="{filename}.pdf"'
        })
    except Exception as e:
        logger.error(f"Error generating resume PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: str, request: Request):
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header")

        response = supabase.table('resumes')\
            .select('optimized_pdf_url')\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Resume not found or not authorized")

        optimized_pdf_url = response.data[0].get('optimized_pdf_url')
        if optimized_pdf_url:
            try:
                file_path = optimized_pdf_url.split('/resumes/')[1].split('?')[0]
                supabase.storage.from_('resumes').remove([file_path])
            except Exception as e:
                logger.warning(f"Warning: Failed to delete file from storage: {str(e)}")

        supabase.table('resumes')\
            .delete()\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        return JSONResponse(content={"success": True})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_file():
    pass
