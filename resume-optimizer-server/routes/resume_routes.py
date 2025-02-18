from flask import Blueprint, request, jsonify
import sentry_sdk
from supabase import create_client, Client
import os
import os
from flask import request, jsonify, make_response
from services.supabase_client import supabase
from services.pdf_generator import PDFGenerator
from supabase import create_client, Client
from flask import request, jsonify, make_response
from loguru import logger

# Create a Blueprint for user routes
resume_routes = Blueprint('resume_routes', __name__)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

@resume_routes.route('/api/resumes/<resume_id>/cover-letter/download', methods=['GET'])
def download_cover_letter(resume_id):
    """Generate and download cover letter PDF from stored content"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        # Get the cover letter content from database
        response = supabase.table('resumes')\
            .select('cover_letter, title')\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            return jsonify({"error": "Resume not found or not authorized"}), 404

        cover_letter = response.data[0].get('cover_letter')
        if not cover_letter:
            return jsonify({"error": "Cover letter not found"}), 404

        # Generate PDF from cover letter content
        pdf_generator = PDFGenerator()
        pdf_data = pdf_generator.create_cover_letter_pdf(cover_letter)

        # Create response with PDF file
        filename = f"cover_letter_{response.data[0].get('title', 'document')}"
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        return response

    except Exception as e:
        print(f"Error generating cover letter PDF: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@resume_routes.route('/api/resumes', methods=['GET'])
def get_resumes():
    """Endpoint to get all resumes"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        # Get limit from query params, default to None (all resumes)
        limit = request.args.get('limit', type=int)

        # Fetch resumes from Supabase
        query = supabase.table('resumes')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)
            
        if limit:
            query = query.limit(limit)

        response = query.execute()

        if not response.data:
            return jsonify([])  # Return empty list if no resumes found

        return jsonify(response.data)
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@resume_routes.route('/api/resumes/<resume_id>/download', methods=['GET'])
def download_resume(resume_id):
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        sentry_sdk.capture_exception(Exception("Test exception 0"))
        # Get the resume content from the database
        supabase_response = supabase.table('resumes')\
            .select('content, title')\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        if not supabase_response.data or len(supabase_response.data) == 0:
            return jsonify({"error": "Resume not found or not authorized"}), 404

        # Get the title and content
        title = supabase_response.data[0].get('title', 'document')
        resume_content = supabase_response.data[0].get('content')
        sentry_sdk.capture_exception(Exception("Test exception 1"))
        
        if not resume_content:
            return jsonify({"error": "Resume content not found"}), 404

        # Generate PDF from resume content
        pdf_generator = PDFGenerator()
        pdf_data = pdf_generator.create_pdf_from_text(resume_content)

        # Log the first 50 characters of the resume content
        logger.info(f"Resume Content (first 50 chars): {resume_content[:50]}...")  # Log first 50 characters

        # Create response with PDF file
        response = make_response(pdf_data)
        filename = f"resume_{title}.pdf"  # Added .pdf extension
        sentry_sdk.capture_message(f"Resume Content (first 50 chars): {resume_content[:50]}", level="info")
        sentry_sdk.capture_message(f"Downloading pdf_data {pdf_data}", level="info")
        sentry_sdk.capture_exception(Exception("Test exception 2"))
        
        # Set the correct headers
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        logger.info(f"Downloading resume: {response}")
        
        # Important: Don't wrap the response in jsonify
        return response

    except Exception as e:
        # For errors, we still want to return JSON
        sentry_sdk.capture_exception(e)
        logger.error(
        f"An error occurred: {str(e)} and user_id: {user_id}",
        exc_info=True,  # Include the full traceback
        )
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@resume_routes.route('/api/resumes/<resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    """Endpoint to delete a resume"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        # First get the resume to check ownership and get the file path
        response = supabase.table('resumes')\
            .select('optimized_pdf_url')\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            return jsonify({"error": "Resume not found or not authorized"}), 404

        optimized_pdf_url = response.data[0].get('optimized_pdf_url')
        if optimized_pdf_url:
            # Extract the file path from the URL
            try:
                file_path = optimized_pdf_url.split('/resumes/')[1].split('?')[0]
                # Delete the file from storage
                supabase.storage.from_('resumes').remove([file_path])
            except Exception as e:
                print(f"Warning: Failed to delete file from storage: {str(e)}")

        # Delete the database record
        supabase.table('resumes')\
            .delete()\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        return jsonify({"success": True})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@resume_routes.route('/upload', methods=['POST'])
def upload_file():
    # Remove the delete endpoint since we're handling it in the frontend
    pass
