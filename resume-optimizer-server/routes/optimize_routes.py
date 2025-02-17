from flask import Blueprint, request, jsonify
from services.openai_optimizer import OpenAIOptimizer
from services.pdf_generator import PDFGenerator
from supabase import create_client, Client
import os
import base64
import re
import time
from flask import request, jsonify
from services.supabase_client import supabase

import tempfile
import time
from supabase import create_client, Client
import datetime
from flask import request, jsonify
from routes.subscription_routes import check_user_credits
from services.linkedin_scraper import LinkedInJobScraper as JobScraper


# Create a Blueprint for optimization routes
optimize_routes = Blueprint('optimize_routes', __name__)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

@optimize_routes.route('/api/optimize', methods=['POST'])
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
            
            # Store the resume content in the resumes table
            resume_data = {
                'user_id': user_id,
                'title': safe_filename,
                'job_url': job_url,
                'content': resume_content,  # Store resume content here
                'analysis': analysis,  # Store only the analysis part
                'cover_letter': cover_letter,  # Store cover letter content
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

        except Exception as e:
            print(f"Error in optimization process: {str(e)}")
            return jsonify({'error': f'Optimization failed: {str(e)}'}), 500

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500
