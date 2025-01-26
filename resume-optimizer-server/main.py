from dotenv import load_dotenv
import os
import openai
import requests
import json
import io
import base64
import pdfplumber
from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from services.linkedin_batch_scraper import LinkedInJobScraper
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
CORS(app, resources={
    r"/*": {  # Allow all routes
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-User-Id"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"]
    }
})  # Enable CORS for all routes with specific configuration

# Enable hot reloading
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

def clean_text(text):
    """Clean extracted text by removing extra spaces and formatting"""
    # Split into lines and clean each line
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        # Remove multiple spaces and tabs
        cleaned_line = ' '.join(word for word in line.split() if word)
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    
    # Join lines back together
    return '\n'.join(cleaned_lines)

def extract_text_from_pdf(file_storage):
    try:
        print(f"[PDF Extraction] Starting PDF text extraction for file: {file_storage.filename}")
        
        # Read the file into a bytes buffer
        pdf_bytes = io.BytesIO(file_storage.read())
        print("[PDF Extraction] Successfully read file into buffer")
        
        text_content = []
        # Use pdfplumber for better text extraction
        with pdfplumber.open(pdf_bytes) as pdf:
            num_pages = len(pdf.pages)
            print(f"[PDF Extraction] PDF has {num_pages} pages")
            
            for i, page in enumerate(pdf.pages):
                # Extract text with better formatting
                page_text = page.extract_text(layout=True)
                if page_text:
                    # Clean the text before adding to content
                    cleaned_text = clean_text(page_text)
                    text_content.append(cleaned_text)
                print(f"[PDF Extraction] Extracted {len(page_text) if page_text else 0} characters from page {i+1}")
        
        # Join all pages with proper spacing
        final_text = "\n\n".join(text_content).strip()
        
        print(f"[PDF Extraction] Total extracted text length: {len(final_text)} characters")
        print("[PDF Extraction] Complete extracted text:")
        print("=" * 80)
        print(final_text)
        print("=" * 80)
        
        return final_text
        
    except Exception as e:
        print(f"[PDF Extraction ERROR] Error extracting text from PDF: {str(e)}")
        raise Exception("Failed to extract text from PDF file")

def generate_with_openai(prompt):
    """Generate optimization suggestions using OpenAI"""
    try:
        print("[OpenAI] Sending request to OpenAI API...")
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Using the original model
            messages=[
                {"role": "system", "content": """You are a professional career advisor that helps optimize resumes and prepare candidates for job opportunities. Your task is to create an ATS-friendly resume that SPECIFICALLY targets this job position.

        CRITICAL - ABSOLUTELY REQUIRED RULES:
        1. JOB MATCHING (HIGHEST PRIORITY):
           ‼️ Analyze the job description thoroughly
           ‼️ Identify key requirements, skills, and qualifications
           ‼️ Reorganize and emphasize resume content to match job requirements
           ‼️ Use similar terminology as the job description
           ‼️ Highlight experiences that directly relate to job requirements
           ‼️ Ensure technical skills match what's asked in the job

        PART 1: OPTIMIZED RESUME
        =======================
        Create a clean, professional resume with these sections:
        1. Contact Information (keep original details)
        2. Professional Summary (concise, impactful)
        3. Technical Skills (prioritize job-relevant skills)
        4. Professional Experience (emphasize relevant achievements)
        5. Education (keep as in original)

        FORMAT RULES:
        - NO headers like "ATS-FRIENDLY" or separator lines
        - Clean, minimal formatting
        - Use bullet points (•) for experience and skills
        - Consistent spacing
        - No tables or columns

        PART 2: IMPROVEMENT ANALYSIS
        ===========================
        Format the analysis EXACTLY as shown below, maintaining the exact structure and markers:

        [SECTION:IMPROVEMENTS]
        • Reorganized Content
        - Restructured sections for better flow
        - Enhanced readability and scannability
        
        • Enhanced Technical Skills
        - Added relevant technologies from job description
        - Prioritized key required skills
        
        • Strengthened Experience
        - Added quantifiable metrics
        - Highlighted leadership roles
        
        • Optimized Keywords
        - Incorporated job-specific terms
        - Added industry-standard variations
        [/SECTION]

        [SECTION:INTERVIEW]
        • Technical Topics
        - Key areas from job requirements
        - System design considerations
        
        • Project Highlights
        - Prepare STAR stories for key projects
        - Focus on technical challenges solved
        
        • Key Questions
        - Prepare for role-specific scenarios
        - Technical implementation details
        
        • Discussion Points
        - Team collaboration examples
        - Code quality practices
        [/SECTION]

        [SECTION:NEXTSTEPS]
        • Skills Development
        - Identify skill gaps
        - Learning resources
        
        • Certifications
        - Relevant technical certifications
        - Industry-specific training
        
        • Portfolio Enhancement
        - Project suggestions
        - Skills to demonstrate
        
        • Industry Knowledge
        - Technology trends
        - Professional networking
        [/SECTION]

        FINAL CHECK - VERIFY:
        1. Resume is SPECIFICALLY TAILORED to job description
        2. ALL experience is included but PRIORITIZED for relevance
        3. Skills and technologies MATCH job requirements
        4. NO fictional or assumed information
        5. Original contact details preserved
        6. Analysis sections use EXACT format with [SECTION:NAME] markers

        ‼️ IMPORTANT: Show the COMPLETE response with both parts clearly separated.
        """},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        print("[OpenAI] Successfully received response")
        print("\n[OpenAI] Response content:")
        print("=" * 80)
        print(response.choices[0].message.content)
        print("=" * 80)
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"[OpenAI ERROR] Error generating optimization suggestions: {str(e)}")
        raise

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

def create_pdf_from_text(text):
    """Convert text to PDF using ReportLab with enhanced formatting"""
    try:
        # Create a BytesIO buffer instead of a temporary file
        buffer = io.BytesIO()
        
        # Set up the document with proper margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Create custom styles
        styles = getSampleStyleSheet()
        
        # Name style
        styles.add(ParagraphStyle(
            name='Name',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor('#2C3E50'),
            fontName='Helvetica-Bold'
        ))
        
        # Section heading style
        styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor('#2C3E50'),
            fontName='Helvetica-Bold'
        ))
        
        # Normal text style
        styles.add(ParagraphStyle(
            name='NormalText',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            fontName='Helvetica',
            leading=14
        ))
        
        # Contact info style
        styles.add(ParagraphStyle(
            name='ContactInfo',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=2,
            fontName='Helvetica',
            textColor=colors.HexColor('#34495E')
        ))
        
        # Parse the text and build the document
        story = []
        lines = text.split('\n')
        current_section = []
        in_contact_section = False
        skip_next = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip ATS header and separator lines
            if "ATS-FRIENDLY" in line or "=" * 10 in line:
                continue
            
            # Remove markers and clean up the text
            line = re.sub(r'^PART \d+:', '', line)  # Remove "PART X:" headers
            line = re.sub(r'\*\*|\#\#', '', line)   # Remove ** and ## markers
            line = line.strip()
            if not line:
                continue
            
            # Handle different sections
            if "PROFESSIONAL SUMMARY" in line.upper():
                story.append(Paragraph("Summary", styles['SectionHeading']))
            elif "PROFESSIONAL EXPERIENCE" in line.upper():
                story.append(Paragraph("Experience", styles['SectionHeading']))
            elif "EDUCATION" in line.upper():
                story.append(Paragraph("Education", styles['SectionHeading']))
            elif "SKILLS" in line.upper():
                story.append(Paragraph("Skills", styles['SectionHeading']))
            elif "CONTACT SECTION" in line.upper():
                continue  # Skip this header
            elif line.startswith('[LinkedIn]'):
                # Clean up LinkedIn URL
                url = re.search(r'\((.*?)\)', line).group(1)
                story.append(Paragraph(f'LinkedIn: {url}', styles['ContactInfo']))
            elif ':' in line and not in_contact_section:
                # Handle contact info
                label, value = line.split(':', 1)
                story.append(Paragraph(
                    f'{label.strip()}: {value.strip()}',
                    styles['ContactInfo']
                ))
            elif line.startswith('•') or line.startswith('-'):
                # Add bullet point
                current_section.append(line[1:].strip())
            else:
                # Add normal paragraph
                if current_section:
                    # Add any collected bullet points before adding new paragraph
                    story.append(ListFlowable(
                        [ListItem(Paragraph(item, styles['NormalText'])) for item in current_section],
                        bulletType='bullet',
                        leftIndent=20,
                        spaceBefore=4,
                        spaceAfter=4
                    ))
                    current_section = []
                
                # Check if this is the name (first non-header line)
                if not story:
                    story.append(Paragraph(line, styles['Name']))
                else:
                    story.append(Paragraph(line, styles['NormalText']))
        
        # Add any remaining bullet points
        if current_section:
            story.append(ListFlowable(
                [ListItem(Paragraph(item, styles['NormalText'])) for item in current_section],
                bulletType='bullet',
                leftIndent=20,
                spaceBefore=4,
                spaceAfter=4
            ))
        
        # Build PDF into the buffer
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
        
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        raise

def extract_job_details(job_url):
    """Extract job details from LinkedIn job URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(job_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract job title
        job_title = soup.find('h1', {'class': 'top-card-layout__title'})
        job_title = job_title.text.strip() if job_title else ''
        
        # Extract company
        company = soup.find('a', {'class': 'topcard__org-name-link'})
        company = company.text.strip() if company else ''
        
        # Extract job description
        job_description = soup.find('div', {'class': 'show-more-less-html__markup'})
        job_description = job_description.text.strip() if job_description else ''
        
        return {
            'job_title': job_title,
            'company': company,
            'job_description': job_description
        }
    except Exception as e:
        print(f"Error extracting job details: {e}")
        return None


def split_ai_response(response):
    """Split OpenAI response into resume and analysis parts"""
    # Find all sections using regex
    sections = re.split(r'\[SECTION:\s*([^\]]+)\]', response)
    
    if len(sections) > 1:
        # First part is the resume content
        resume_content = sections[0].strip()
        
        # Combine all sections into analysis
        analysis_parts = []
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                section_name = sections[i].strip()
                section_content = sections[i + 1].strip()
                analysis_parts.append(f"[{section_name}]\n{section_content}")
        
        analysis = "\n\n".join(analysis_parts)
    else:
        # If no sections found, treat everything as resume content
        resume_content = response.strip()
        analysis = ""
    
    return resume_content, analysis

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

        scraper = LinkedInJobScraper()
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

        scraper = LinkedInJobScraper()
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
        scraper = LinkedInJobScraper()
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

@app.route('/optimize', methods=['POST'])
def optimize_resume():
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 401

        # Get the uploaded file and job details
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file provided'}), 400
        
        resume_file = request.files['resume']
        if not resume_file or not resume_file.filename:
            return jsonify({'error': 'No resume file selected'}), 400

        # Get job details from form data
        job_url = request.form.get('job_url')
        
        # Extract job details from LinkedIn URL if available
        job_title = None
        company = None
        job_description = None
        
        if job_url and 'linkedin.com' in job_url:
            try:
                job_details = extract_job_details(job_url)
                if job_details:
                    job_title = job_details.get('job_title')
                    company = job_details.get('company')
                    job_description = job_details.get('job_description')
            except Exception as e:
                print(f"Error extracting job details: {str(e)}")
                # Continue without job details if extraction fails

        # Extract text from PDF
        resume_text = extract_text_from_pdf(resume_file)
        if not resume_text:
            return jsonify({'error': 'Failed to extract text from PDF'}), 400

        # Get optimization suggestions
        try:
            optimization_prompt = f"""
            Please optimize this resume and provide improvement suggestions. Format your response in clear sections as follows:

            1. First, provide the optimized resume content with proper formatting.

            2. Then add the following sections, each starting with its section marker:

            [SECTION: IMPROVEMENTS]
            List specific improvements made to the resume and why they enhance it.

            [SECTION: INTERVIEW]
            Provide preparation tips for interviews based on this resume.

            [SECTION: NEXTSTEPS]
            Suggest next steps for career development and resume enhancement.
            """
            
            if job_title and company:
                optimization_prompt += f" Optimize specifically for the position of {job_title} at {company}."
            
            optimization_prompt += f"""
            
            Original Resume:
            {resume_text}
            """
            
            if job_description:
                optimization_prompt += f"""
                
                Job Description:
                {job_description}
                """
            
            optimization_result = generate_with_openai(optimization_prompt)
            
            # Split the result into resume content and analysis
            resume_content, analysis = split_ai_response(optimization_result)
            
            # Create PDF from optimized resume content only
            pdf_data = create_pdf_from_text(resume_content)
            
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
                if job_url and job_title and company:
                    print(f"Creating job application with details:", {
                        'job_title': job_title,
                        'company': company,
                        'has_description': bool(job_description)
                    })
                    
                    try:
                        job_data = {
                            'user_id': user_id,
                            'resume_id': resume_id,
                            'job_title': job_title,
                            'company': company,
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
        signed_url_response = supabase.storage\
            .from_('resumes')\
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

def main():
    """Main function to run the application"""
    print("\n=== Starting Resume Optimizer Server ===")
    
    # Validate environment
    if not validate_environment():
        print("\nPlease set all required environment variables and try again.")
        return
    
    # Configuration
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', 5050))
    debug = True  # Force debug mode for hot reloading
    
    print(f"\nServer Configuration:")
    print(f"- Host: {host}")
    print(f"- Port: {port}")
    print(f"- Debug Mode: {debug}")
    print(f"- Hot Reloading: Enabled")
    
    print("\nAvailable Endpoints:")
    print("- GET / - API information")
    print("- GET /health - Health check")
    print("- POST /get-job-details - Get job details from LinkedIn")
    print("- POST /optimize - Optimize resume")
    print("- GET /api/resumes - Get user's resumes")
    print("- GET /api/resumes/<id>/download - Download resume")
    print("- DELETE /api/resumes/<id> - Delete resume")
    print("- GET /job/<job_id> - Get job details by ID")
    print("- GET /api/jobs - Get user's jobs")
    print("- POST /api/jobs - Create new job application")
    print("- PUT /api/jobs/<job_id>/status - Update job application status")
    
    # Run the application with hot reloading
    app.run(
        host=host,
        port=port,
        debug=True,
        use_reloader=True,
        threaded=True
    )

if __name__ == '__main__':
    main()