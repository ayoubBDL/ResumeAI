from dotenv import load_dotenv
import os
import openai
import requests
import json
import io
import base64
import pdfplumber
from flask import Flask, request, jsonify, make_response, send_file
from services.linkedin_batch_scraper import LinkedInJobScraper
from services.linkedin_scraper import LinkedInJobScraper as JobScraper
from services.supabase_client import supabase
from reportlab.lib import colors
from services.pdf_generator import PDFGenerator
from services.openai_optimizer import OpenAIOptimizer
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

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables")
openai.api_key = api_key

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
if not supabase_url or not supabase_key:
    raise ValueError(f"Supabase credentials not found. URL: {'set' if supabase_url else 'missing'}, Key: {'set' if supabase_key else 'missing'}")

supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)
CORS(
    app,
    origins=[os.getenv('CLIENT_URL', 'https://jobsageai.netlify.app')],  # Allow only the specified origin
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Allow these HTTP methods
    allow_headers=["Content-Type", "Authorization", "X-User-Id"],  # Allow these headers
    supports_credentials=True,  # Allow credentials (e.g., cookies)
    expose_headers=["Content-Type", "Authorization"]  # Expose these headers to the client
)

# Enable hot reloading
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# At the top with other environment checks
if not os.getenv('PAYPAL_API_URL'):
    raise ValueError("PayPal API URL not found in environment variables")

def generate_with_ollama(prompt):
    """Generate optimization suggestions using Ollama"""
    try:
        print("[Ollama] Sending request to Ollama API...")
        response = requests.post('http://localhost:11434/api/generate',
                               json={
                                   "model": "mistral",
                                   "prompt": prompt,
                                   "stream": False
                               })
        response.raise_for_status()
        print("[Ollama] Successfully received response")
        return response.json()['response']
    except Exception as e:
        print(f"[Ollama ERROR] Error generating suggestions: {str(e)}")
        raise

@app.route('/')
def home():
    """Root endpoint providing API information"""
    return jsonify({
        "message": "Resume Optimizer API is running",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "POST /get-job-details": "Get job details from LinkedIn",
            "POST /optimize": "Optimize resume for job posting",
            "POST /scrape-jobs": "Scrape jobs from LinkedIn",
            "POST /scrape-job-url": "Scrape job by URL",
            "POST /search-similar-jobs": "Search for similar jobs",
            "GET /job/<job_id>": "Get job details by ID",
            "GET /api/jobs": "Get user's jobs",
            "POST /api/jobs": "Create new job application",
            "PUT /api/jobs/<job_id>/status": "Update job application status"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

@app.route('/get-job-details', methods=['POST'])
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

@app.route('/scrape-jobs', methods=['POST'])
def scrape_jobs():
    """Endpoint to scrape jobs from LinkedIn based on search criteria"""
    try:
        data = request.get_json()
        if not data or 'search_queries' not in data:
            return jsonify({
                "success": False,
                "error": "Missing search_queries in request body"
            }), 400

        max_jobs = data.get('max_jobs', 25)
        scraper = LinkedInJobScraper()
        jobs = scraper.scrape_jobs(data['search_queries'], max_jobs)

        return jsonify({
            "success": True,
            "data": {
                "jobs": jobs,
                "count": len(jobs)
            }
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/scrape-job-url', methods=['POST'])
def scrape_job_url():
    """Endpoint to scrape a job from a specific LinkedIn URL"""
    try:
        data = request.get_json()
        if not data or 'job_url' not in data:
            return jsonify({
                "success": False,
                "error": "Missing job_url in request body"
            }), 400

        scraper = JobScraper()
        job_details = scraper.scrape_job_by_url(data['job_url'])

        if job_details is None:
            return jsonify({
                "success": False,
                "error": "Failed to scrape job details"
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

@app.route('/search-similar-jobs', methods=['POST'])
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

@app.route('/api/optimize', methods=['POST'])
def optimize_resume():
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 401

        # Check credits and subscription
        has_credits, credits_or_error = check_user_credits(user_id)
        if not has_credits:
            return jsonify(credits_or_error), 403

        # Store credits for deduction later if not enterprise user
        credits_remaining = credits_or_error if isinstance(credits_or_error, int) else None
        
        # Get the uploaded file and job details
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        resume_file = request.files['resume']
        if not resume_file or not resume_file.filename:
            return jsonify({'error': 'No resume file selected'}), 400

        # Get job details from form data
        job_url = request.form.get('job_url')
        job_description = request.form.get('job_description')
        
        # Extract job details from LinkedIn URL if available
        job_title = None
        company = None
        
        if job_url and 'linkedin.com' in job_url:
            try:
                scraper = JobScraper()
                job_details = scraper.extract_job_details(job_url)
                if job_details:
                    job_title = job_details.get('job_title')
                    company = job_details.get('company')
                    job_description = job_details.get('job_description')
            except Exception as e:
                print(f"Error extracting job details: {str(e)}")
        elif job_description:
            # If we only have job description, proceed without title/company
            print(f"Processing with job description only")
        else:
            return jsonify({'error': 'Please provide either a job URL or description'}), 400

        # Extract text from PDF
        pdf_generator = PDFGenerator()
        resume_text = pdf_generator.extract_text_from_pdf(resume_file)
        if not resume_text:
            return jsonify({'error': 'Failed to extract text from PDF'}), 400

        # Get optimization suggestions
        try:
            openai_optimizer = OpenAIOptimizer()
            optimization_result = openai_optimizer.generate_with_openai(job_title, company, resume_text, job_description)
            
            # Split the result into resume content and analysis
            resume_content, analysis = openai_optimizer.split_ai_response(optimization_result)

            cover_letter = openai_optimizer.generate_cover_letter(resume_text, job_description, job_title, company)
            
            # Create PDF from optimized resume content only
            pdf_data = pdf_generator.create_pdf_from_text(resume_content)
            
            # Convert PDF data to base64 for response
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            
            # Generate safe filename
            safe_filename = re.sub(r'[^a-zA-Z0-9.-]', '_', resume_file.filename)
            filename = f"{int(time.time())}_{safe_filename}"
            
            # Create temporary file to store PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='wb') as temp_pdf:
                temp_pdf.write(pdf_data)
                temp_pdf.flush()
                
                # Upload PDF to Supabase Storage
                try:
                    with open(temp_pdf.name, 'rb') as pdf_file:
                        upload_result = supabase.storage \
                            .from_('resumes') \
                            .upload(
                                path=filename,
                                file=pdf_file,
                                file_options={"content-type": "application/pdf"}
                            )
                    
                    if not upload_result:
                        raise Exception("Failed to upload PDF to storage")

                except Exception as upload_error:
                    print(f"Upload error: {str(upload_error)}")
                    raise upload_error
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_pdf.name)
                    except:
                        pass

            # Get signed URL for the uploaded PDF
            try:
                url_result = supabase.storage \
                    .from_('resumes') \
                    .create_signed_url(filename, 60 * 60)  # 1 hour expiry

                if not url_result or 'signedURL' not in url_result:
                    raise Exception("Failed to get signed URL")

                signed_url = url_result['signedURL']
            except Exception as url_error:
                print(f"Signed URL error: {str(url_error)}")
                raise url_error

            # Create resume record in database
            try:
                resume_data = {
                    'user_id': user_id,
                    'title': safe_filename,
                    'job_url': job_url,
                    'optimized_pdf_url': signed_url,
                    'analysis': analysis,  # Store only the analysis part
                    'cover_letter': cover_letter,
                    'status': 'completed'
                }
                
                resume_result = supabase \
                    .table('resumes') \
                    .insert(resume_data) \
                    .execute()

                if not resume_result.data:
                    raise Exception("Failed to create resume record")

                resume_id = resume_result.data[0]['id']

                # Create job application if we have job details
                if job_description:
                    print(f"Creating job application with details:", {
                        'job_title': job_title or 'Untitled Position',
                        'company': company or 'Unknown Company',
                        'has_description': bool(job_description)
                    })
                    
                    try:
                        job_data = {
                            'user_id': user_id,
                            'resume_id': resume_id,
                            'job_title': job_title or 'Untitled Position',
                            'company': company or 'Unknown Company',
                            'job_description': job_description,
                            'job_url': job_url,
                            'status': 'pending'
                        }
                        
                        job_result = supabase \
                            .table('job_applications') \
                            .insert(job_data) \
                            .execute()
                            
                        print(f"Job application created:", job_result.data if job_result else None)
                    except Exception as job_error:
                        print(f"Error creating job application: {str(job_error)}")
                        # Don't raise the error as this is not critical
                else:
                    print(f"Skipping job application - missing required fields:", {
                        'has_url': bool(job_url),
                        'has_title': bool(job_title),
                        'has_company': bool(company)
                    })

                # Since optimization was successful, deduct one credit if not enterprise user
                if credits_remaining is not None:  # Only deduct if user is using credits (not enterprise)
                    supabase.table('usage_credits').update({
                        'credits_remaining': credits_remaining - 1,
                        'updated_at': datetime.datetime.utcnow().isoformat()
                    }).eq('user_id', user_id).execute()
                
                # Return success response with base64 PDF data and resume details
                return jsonify({
                    'success': True,
                    'pdf_data': pdf_base64,
                    'analysis': analysis,  # Return only the analysis part
                    'resume_id': resume_id,
                    'title': safe_filename,
                    'created_at': datetime.datetime.now().isoformat(),
                    'job_url': job_url,
                    'status': 'completed'
                })

            except Exception as db_error:
                print(f"Database error: {str(db_error)}")
                raise db_error

        except Exception as e:
            print(f"Error in optimization process: {str(e)}")
            return jsonify({'error': f'Optimization failed: {str(e)}'}), 500

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/resumes/<resume_id>/cover-letter/download', methods=['GET', 'OPTIONS'])
def download_cover_letter(resume_id):
    """Generate and download cover letter PDF from stored content"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

@app.route('/api/resumes', methods=['GET', 'OPTIONS'])
def get_resumes():
    """Endpoint to get all resumes"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

@app.route('/api/resumes/<resume_id>/download', methods=['GET', 'OPTIONS'])
def download_resume(resume_id):
    """Endpoint to get a signed URL for downloading a resume PDF"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        # First verify the resume belongs to the user and get the PDF URL
        response = supabase.table('resumes')\
            .select('optimized_pdf_url')\
            .eq('id', resume_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            return jsonify({"error": "Resume not found or not authorized"}), 404

        optimized_pdf_url = response.data[0].get('optimized_pdf_url')
        if not optimized_pdf_url:
            return jsonify({"error": "Resume file not found"}), 404

        # Extract the file path from the stored URL
        # URL format: https://<project>.supabase.co/storage/v1/object/sign/resumes/<filename>?token=...
        try:
            file_path = optimized_pdf_url.split('/resumes/')[1].split('?')[0]
        except:
            return jsonify({"error": "Invalid file URL format"}), 500

        # Generate a fresh signed URL
        signed_url_response = supabase.storage \
            .from_('resumes') \
            .create_signed_url(file_path, 300)  # URL valid for 5 minutes

        if not signed_url_response or 'signedURL' not in signed_url_response:
            return jsonify({"error": "Failed to generate download URL"}), 500

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

@app.route('/api/resumes/<resume_id>', methods=['DELETE', 'OPTIONS'])
def delete_resume(resume_id):
    """Endpoint to delete a resume"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

@app.route('/upload', methods=['POST'])
def upload_file():
    # Remove the delete endpoint since we're handling it in the frontend
    pass

@app.route('/job/<job_id>', methods=['GET', 'OPTIONS'])
def get_job(job_id):
    """Endpoint to get job details by ID"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

@app.route('/api/jobs', methods=['GET', 'POST', 'OPTIONS'])
def jobs():
    """Handle jobs endpoints"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

@app.route('/api/jobs/<job_id>/download', methods=['GET', 'OPTIONS'])
def download_job_resume(job_id):
    """Endpoint to get a signed URL for downloading a resume PDF"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

@app.route('/api/jobs/<job_id>/status', methods=['PUT', 'OPTIONS'])
def update_job_status(job_id):
    """Update job application status"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'PUT,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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

@app.route("/api/jobs/<job_id>", methods=["DELETE"])
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

@app.route('/api/credits', methods=['GET'])
def get_user_credits():
    """Get user's current credit balance"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        credits_response = supabase.table('usage_credits').select('credits_remaining').eq('user_id', user_id).execute()
        if len(credits_response.data) == 0:
            # Create initial credits for user if not exists
            supabase.table('usage_credits').insert({
                'user_id': user_id,
                'credits_remaining': 2,
                'created_at': datetime.datetime.utcnow().isoformat(),
                'updated_at': datetime.datetime.utcnow().isoformat()
            }).execute()
            return jsonify({"credits": 2})

        return jsonify({
            "credits": credits_response.data[0]['credits_remaining']
        })

    except Exception as e:
        print(f"Error getting user credits: {str(e)}")
        return jsonify({"error": "Failed to get user credits"}), 500

@app.route('/api/credits/initialize', methods=['POST'])
def initialize_credits():
    """Initialize credits for a new user"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        # Check if user already has credits
        credits_response = supabase.table('usage_credits').select('credits_remaining').eq('user_id', user_id).execute()
        if len(credits_response.data) > 0:
            return jsonify({"error": "Credits already initialized for this user"}), 400

        # Initialize credits for new user
        supabase.table('usage_credits').insert({
            'user_id': user_id,
            'credits_remaining': 2,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'updated_at': datetime.datetime.utcnow().isoformat()
        }).execute()

        return jsonify({
            "success": True,
            "message": "Credits initialized successfully",
            "credits": 2
        })

    except Exception as e:
        print(f"Error initializing credits: {str(e)}")
        return jsonify({"error": "Failed to initialize credits"}), 500

@app.route('/api/credits/purchase', methods=['POST'])
def purchase_credits():
    """Purchase credits based on selected plan"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        data = request.get_json()

        # Calculate credits based on plan
        min_credits = 5
        requested_credits = data.get('credits', min_credits)
        if requested_credits < min_credits:
            return jsonify({"error": f"Minimum credit purchase is {min_credits}"}), 400
        credits = requested_credits

        # Get current credits
        credits_response = supabase.table('usage_credits').select('credits_remaining').eq('user_id', user_id).execute()
        print("Credits response:", credits_response)

        if not credits_response.data:
            # Create new record if it doesn't exist
            new_credits = credits
            supabase.table('usage_credits').insert({
                'user_id': user_id,
                'credits_remaining': new_credits
            }).execute()
        else:
            # Update existing record
            current_credits = credits_response.data[0]['credits_remaining']
            new_credits = current_credits + credits
            print(f"Updating credits from {current_credits} to {new_credits}")
            supabase.table('usage_credits').update({
                'credits_remaining': new_credits
            }).eq('user_id', user_id).execute()

        return jsonify({
            "success": True,
            "message": f"Successfully added {credits} credits",
            "new_balance": new_credits
        })

    except Exception as e:
        print(f"Error purchasing credits: {str(e)}")
        return jsonify({"error": "Failed to purchase credits"}), 500

def generate_paypal_token() -> str:
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise Exception("Missing PayPal client ID or secret in environment variables.")
    
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_header}",
    }
    
    response = requests.post(url, headers=headers, data="grant_type=client_credentials")
    
    if response.status_code == 200:
        return response.json().get("access_token", "")
    else:
        raise Exception(f"Failed to generate token: {response.status_code}, {response.text}")

@app.route('/api/subscriptions', methods=['GET'])
def get_subscription():
    """Get user's current subscription status"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        # Get subscription from Supabase - now without status filter
        subscription_response = supabase.table('subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()

        # If no subscription found at all, return early
        if not subscription_response.data or len(subscription_response.data) == 0:
            return jsonify({
                "has_subscription": False,
                "subscription": None
            })

        # Get the subscription data
        subscription = subscription_response.data[0]
        paypal_subscription_id = subscription.get('paypal_subscription_id')

        # If no PayPal subscription ID, return just the Supabase data
        if not paypal_subscription_id:
            return jsonify({
                "has_subscription": subscription.get('status') == 'active',
                "subscription": subscription
            })

        # Check PayPal status only if subscription was active
        if subscription.get('status') == 'active':
            access_token = generate_paypal_token()
            if not access_token:
                return jsonify({"error": "Failed to generate Paypal access token"}), 500

            url = f"{os.getenv('PAYPAL_API_URL')}/v1/billing/subscriptions/{paypal_subscription_id}"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                paypal_status = response.json().get('status', '').lower()
                
                # If cancelled in PayPal but active in Supabase, update Supabase
                if paypal_status in ['cancelled', 'suspended', 'expired']:
                    now = datetime.datetime.utcnow()
                    supabase.table('subscriptions')\
                        .update({
                            'status': paypal_status,
                            'updated_at': now.isoformat(),
                            'cancelled_at': now.isoformat()
                        })\
                        .eq('id', subscription.get('id'))\
                        .execute()

                    return jsonify({
                        "has_subscription": False,
                        "subscription": subscription,
                        "paypal_subscription": response.json()
                    })

            return jsonify({
                "has_subscription": True,
                "subscription": subscription,
                "paypal_subscription": response.json()
            })
        
        # For inactive subscriptions, just return the data without PayPal check
        return jsonify({
            "has_subscription": False,
            "subscription": subscription
        })

    except Exception as e:
        print(f"Error getting subscription: {str(e)}")
        return jsonify({"error": "Failed to get subscription status"}), 500

@app.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    """Create or update user subscription"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        data = request.get_json()
        if not data or 'plan_type' not in data:
            return jsonify({"error": "Plan type is required"}), 400

        if not data or 'subscriptionId' not in data:
            return jsonify({"error": "subscriptionId is required"}), 400

        plan_type = data['plan_type']
        
        # Cancel any existing active subscriptions
        supabase.table('subscriptions')\
            .update({'status': 'cancelled'})\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()

        # Create new subscription
        now = datetime.datetime.utcnow()
        subscription_data = {
            'user_id': user_id,
            'plan_type': plan_type,
            'paypal_subscription_id': data['subscriptionId'],
            'status': 'active',
            'current_period_start': now.isoformat(),
            'current_period_end': (now + datetime.timedelta(days=30)).isoformat(),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }

        subscription_result = supabase.table('subscriptions')\
            .insert(subscription_data)\
            .execute()

        # Update user credits based on plan
        credits = 0
        if plan_type == 'free':
            credits = 2
        elif plan_type == 'pro':
            credits = 50
        elif plan_type == 'yearly':
            credits = 9999
        elif plan_type == 'enterprise':
            credits = 999999

        # Update or create credits
        credits_response = supabase.table('usage_credits').select('*').eq('user_id', user_id).execute()
        if len(credits_response.data) == 0:
            supabase.table('usage_credits').insert({
                'user_id': user_id,
                'credits_remaining': credits,
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }).execute()
        else:
            supabase.table('usage_credits').update({
                'credits_remaining': credits,
                'updated_at': now.isoformat()
            }).eq('user_id', user_id).execute()

        return jsonify({
            "success": True,
            "message": f"Successfully subscribed to {plan_type} plan",
            "subscription": subscription_result.data[0] if subscription_result.data else None,
            "credits": credits
        })

    except Exception as e:
        print(f"Error creating subscription: {str(e)}")
        return jsonify({"error": "Failed to create subscription"}), 500

@app.route('/api/cancel-subscription', methods=['POST', 'OPTIONS'])
def cancel_subscription():
    """Cancel user subscription"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "User ID is required"
            }), 401

        # Get the active subscription for the user
        subscription_result = supabase.table('subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()

        if not subscription_result.data:
            return jsonify({
                "success": False,
                "error": "No active subscription found"
            }), 404

        subscription = subscription_result.data[0]
        subscription_id = subscription.get('id')
        paypal_subscription_id = subscription.get('paypal_subscription_id')

        if not subscription_id:
            return jsonify({
                "success": False,
                "error": "Invalid subscription ID"
            }), 400

        if not paypal_subscription_id:
            return jsonify({
                "success": False,
                "error": "No PayPal subscription ID found"
            }), 400

        # Generate PayPal access token
        try:
            access_token = generate_paypal_token()
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Failed to generate PayPal token: {str(e)}"
            }), 500

        # First check subscription status in PayPal
        status_url = f"{os.getenv('PAYPAL_API_URL')}/v1/billing/subscriptions/{paypal_subscription_id}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        status_response = requests.get(status_url, headers=headers)
        print("PayPal Status Response:", status_response.json())

        if status_response.status_code == 200:
            paypal_status = status_response.json().get('status', '').lower()
            
            # If already cancelled in PayPal, just update Supabase
            if paypal_status in ['cancelled', 'suspended', 'expired']:
                now = datetime.datetime.utcnow()
                supabase.table('subscriptions')\
                    .update({
                        'status': 'cancelled',
                        'updated_at': now.isoformat(),
                        'cancelled_at': now.isoformat()
                    })\
                    .eq('id', subscription_id)\
                    .execute()

                return jsonify({
                    "success": True,
                    "message": "Subscription status synchronized with PayPal"
                })

        # If not cancelled, proceed with cancellation
        cancel_url = f"{os.getenv('PAYPAL_API_URL')}/v1/billing/subscriptions/{paypal_subscription_id}/cancel"
        cancel_response = requests.post(
            cancel_url,
            headers=headers,
            json={"reason": "Cancelled by user"}
        )

        print("PAYPAL REQUEST", cancel_url)
        print("PAYPAL RESPONSE STATUS", cancel_response.status_code)
        print("PAYPAL RESPONSE CONTENT", cancel_response.content)

        if cancel_response.status_code not in [204, 200]:
            return jsonify({
                "success": False,
                "error": f"Failed to cancel PayPal subscription. Status: {cancel_response.status_code}"
            }), 500

        # Update subscription status in Supabase
        now = datetime.datetime.utcnow()
        supabase.table('subscriptions')\
            .update({
                'status': 'cancelled',
                'updated_at': now.isoformat(),
                'cancelled_at': now.isoformat()
            })\
            .eq('id', subscription_id)\
            .execute()

        return jsonify({
            "success": True,
            "message": "Subscription cancelled successfully"
        })

    except Exception as e:
        print(f"Error cancelling subscription: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def check_user_credits(user_id):
    """Check if user has credits in Supabase"""
    try:
        credits_response = supabase.table('usage_credits')\
            .select('credits_remaining')\
            .eq('user_id', user_id)\
            .execute()
            
        # If no credits record exists or credits <= 0
        if len(credits_response.data) == 0 or credits_response.data[0]['credits_remaining'] <= 0:
            return False, {
                "error": "Insufficient credits",
                "message": "You have no credits remaining. Please purchase more credits to continue.",
                "action": "purchase_required",
                "redirect_url": "/dashboard/billing",
                "current_credits": credits_response.data[0]['credits_remaining'] if credits_response.data else 0
            }

        return True, credits_response.data[0]['credits_remaining']

    except Exception as e:
        print(f"Error checking user credits: {str(e)}")
        return False, {"error": "Failed to check credits"}

def validate_environment():
    """Validate required environment variables"""
    required_vars = ['OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        return False
    return True

@app.route('/api/create-paypal-subscription', methods=['POST'])
def create_paypal_subscription():
    """Create or update user subscription"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        data = request.get_json()
        if not data or 'plan_id' not in data:
            return jsonify({"error": "Plan ID is required"}), 400
        if not data or 'access_token' not in data:
            return jsonify({"error": "access_token is required"}), 400
        plan_id = data['plan_id']
        access_token = data['access_token']
        
        url = f'https://api-m.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}'

        if not access_token:
            return jsonify({"error": "Failed to generate Paypal access token"}), 500
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Prefer': 'return=representation',
            'Authorization': f'Bearer {access_token}',
            'PayPal-Request-Id': 'SUBSCRIPTION-21092019-001',
        }

        body = {
            "plan_id": plan_id,
            "start_time": "2025-10-20T12:00:00Z",
            "application_context": {
                "user_action": "SUBSCRIBE_NOW",
                "return_url": "https://localhost:5173/success",
                "cancel_url": "https://localhost:5173/cancel"
            }
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code != 201:
            return jsonify({"error": "Failed to create subscription"}), 500

        return jsonify({
            "success": True,
            "subscription": response.json()
        })

    except Exception as e:
        print(f"Error creating subscription: {str(e)}")
        return jsonify({"error": "Failed to create subscription"}), 500

@app.route('/api/users/profile', methods=['PUT', 'OPTIONS'])
def update_user_profile():
    """Update user profile"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'PUT,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        data = request.get_json()
        if not data or 'full_name' not in data:
            return jsonify({
                "success": False,
                "error": "Missing full_name in request body"
            }), 400

        # Update user metadata in Supabase
        update_result = supabase.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": {"name": data['full_name']}}
        )

        if not update_result.user:
            return jsonify({
                "success": False,
                "error": "Failed to update user profile"
            }), 500

        # Get updated user data from Supabase
        user_response = supabase.auth.admin.get_user_by_id(user_id)
        if not user_response.user:
            return jsonify({
                "success": False,
                "error": "Failed to fetch updated user data"
            }), 500

        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "user_metadata": user_response.user.user_metadata,
                "app_metadata": user_response.user.app_metadata
            }
        })

    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def main():
    """Main function to run the application"""
    print("\n=== Starting Resume Optimizer Server ===")
    
    # Validate environment
    if not validate_environment():
        print("\nPlease set all required environment variables and try again.")
        return
    
     # Configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 10000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"\nServer Configuration:")
    print(f"- Host: {host}")
    print(f"- Port: {port}")
    print(f"- Debug Mode: {debug}")
    print(f"- Client URL: {os.getenv('CLIENT_URL')}")

    
    if debug:
        # Run with Flask's built-in server for development
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            threaded=True
        )
    else:
        # Run with Waitress for production
        print("\nRunning in production mode with Waitress...")
        serve(app, host=host, port=port)

if __name__ == '__main__':
    main()