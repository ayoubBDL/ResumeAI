from flask import Blueprint, request, jsonify
from services.linkedin_scraper import LinkedInJobScraper
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import os
import openai
import requests
import json
import io
import base64
import pdfplumber
from flask import Flask, request, jsonify, make_response, send_file
from services.supabase_client import supabase
from reportlab.lib import colors

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle, HRFlowable
import re
import tempfile
import time
from bs4 import BeautifulSoup
from supabase import create_client, Client
import datetime
import logging
from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from requests.auth import HTTPBasicAuth
from waitress import serve 
from services.linkedin_batch_scraper import LinkedInJobScraper
from services.linkedin_scraper import LinkedInJobScraper as JobScraper

# Create a Blueprint for job routes
job_routes = Blueprint('job_routes', __name__)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

@job_routes.route('/job/<job_id>', methods=['GET'])
def get_job(job_id):
    """Endpoint to get job details by ID"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        # Fetch job details from Supabase with associated resume data
        response = supabase.table('job_applications')\
            .select('*, resume:resumes(id, analysis, title, created_at)')\
            .eq('id', job_id)\
            .eq('user_id', user_id)\
            .single()\
            .execute()

        if not response.data:
            return jsonify({
                "success": False,
                "error": "Job not found or not authorized"
            }), 404

        # Transform the response to include resume analysis
        job_data = {**response.data}
        if job_data.get('resume'):
            job_data['analysis'] = job_data['resume'].get('analysis')

        return jsonify({
            "success": True,
            "data": job_data
        })

    except Exception as e:
        print(f"Error getting job details: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@job_routes.route('/api/jobs', methods=['GET', 'POST'])
def jobs():
    """Handle jobs endpoints"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        if request.method == 'GET':
            # Get jobs from Supabase with resume data
            response = supabase.table('job_applications')\
                .select('*, resume:resumes(id, analysis, title, created_at, optimized_pdf_url)')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .execute()

            if not response.data:
                return jsonify([])

            # Transform the response to include resume analysis
            jobs = []
            for job in response.data:
                job_data = {**job}
                if job.get('resume'):
                    resume = job['resume']
                    job_data['analysis'] = resume.get('analysis')
                    job_data['resume_title'] = resume.get('title')
                    job_data['resume_id'] = resume.get('id')
                jobs.append(job_data)

            return jsonify(jobs)

        elif request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "Missing request body"
                }), 400

            required_fields = ['job_title', 'company', 'job_description', 'job_url']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }), 400

            # Get the latest resume for this user
            resume_response = supabase.table('resumes')\
                .select('id')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()

            resume_id = resume_response.data[0]['id'] if resume_response.data else None

            # Save job to Supabase
            job_data = {
                'user_id': user_id,
                'resume_id': resume_id,  # Link to the resume we just created
                'company': data['company'],
                'job_title': data['job_title'],
                'job_url': data['job_url'],
                'job_description': data['job_description'],
                'status': 'new',
                'created_at': 'now()',
                'updated_at': 'now()'
            }

            response = supabase.table('job_applications')\
                .insert(job_data)\
                .execute()

            if not response.data:
                return jsonify({
                    "success": False,
                    "error": "Failed to save job"
                }), 500

            return jsonify({
                "success": True,
                "data": response.data[0]
            })

    except Exception as e:
        print(f"Error handling jobs request: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@job_routes.route('/api/jobs/<job_id>/download', methods=['GET'])
def download_job_resume(job_id):
    """Endpoint to get a signed URL for downloading a resume PDF"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        # First verify the job belongs to the user and get the resume ID
        response = supabase.table('job_applications')\
            .select('resume:resumes(optimized_pdf_url)')\
            .eq('id', job_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            return jsonify({
                "success": False,
                "error": "Resume not found or not authorized"
            }), 404

        optimized_pdf_url = response.data[0]['resume'].get('optimized_pdf_url')
        if not optimized_pdf_url:
            return jsonify({
                "success": False,
                "error": "Resume file not found"
            }), 404

        # Extract the file path from the URL
        try:
            file_path = optimized_pdf_url.split('/resumes/')[1].split('?')[0]
        except:
            return jsonify({
                "success": False,
                "error": "Invalid file URL format"
            }), 500

        # Generate a fresh signed URL
        signed_url_response = supabase.storage\
            .from_('resumes')\
            .create_signed_url(file_path, 300)  # URL valid for 5 minutes

        if not signed_url_response or 'signedURL' not in signed_url_response:
            return jsonify({
                "success": False,
                "error": "Failed to generate download URL"
            }), 500

        return jsonify({
            "success": True,
            "url": signed_url_response['signedURL']
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@job_routes.route('/api/jobs/<job_id>/status', methods=['PUT'])
def update_job_status(job_id):
    """Update job application status"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                "success": False,
                "error": "Missing status in request body"
            }), 400

        # Verify valid status
        valid_statuses = ['new', 'applied', 'interviewing', 'offered', 'rejected']
        if data['status'] not in valid_statuses:
            return jsonify({
                "success": False,
                "error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }), 400

        # Update job in Supabase
        response = supabase.table('job_applications')\
            .update({'status': data['status'], 'updated_at': 'now()'})\
            .eq('id', job_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            return jsonify({
                "success": False,
                "error": "Job not found or not authorized"
            }), 404

        return jsonify({
            "success": True,
            "data": response.data[0]
        })

    except Exception as e:
        print(f"Error updating job status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@job_routes.route("/api/jobs/<job_id>", methods=["DELETE"])
def delete_job(job_id):
    try:
        # Get user_id from header
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 401

        # Delete the job application from Supabase
        response = supabase.table('job_applications').delete().eq('id', job_id).eq('user_id', user_id).execute()
        
        if not response.data:
            return jsonify({
                "success": False,
                "error": "Job application not found or unauthorized"
            }), 404

        return jsonify({
            "success": True,
            "message": "Job application deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting job application: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@job_routes.route('/search-similar-jobs', methods=['POST'])
def search_similar_jobs():
    """Endpoint to search for similar jobs based on a reference LinkedIn job URL"""
    try:
        data = request.get_json()
        if not data or 'job_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing job_url in request body"
            }), 400

        max_jobs = data.get('max_jobs', 25)
        scraper = JobScraper()
        similar_jobs = scraper.search_similar_jobs(data['job_url'], max_jobs)

        return jsonify({
            "success": True,
            "data": {
                "jobs": similar_jobs,
                "count": len(similar_jobs)
            }
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@job_routes.route('/get-job-details', methods=['POST'])
def get_job_details():
    """Endpoint to get job details from a LinkedIn job URL"""
    try:
        data = request.get_json()
        if not data or 'job_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing job_url in request body"
            }), 400

        scraper = JobScraper()
        job_details = scraper.get_job_details(data['job_url'])

        if job_details is None:
            return jsonify({
                "success": False,
                "error": "Failed to get job details"
            }), 404

        return jsonify({
            "success": True,
            "data": job_details
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
