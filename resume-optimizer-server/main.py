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

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables")
openai.api_key = api_key

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
        Provide a structured analysis with these sections:

        1. KEY IMPROVEMENTS MADE:
        • List specific improvements made to the resume (use bullet points)
        • Explain how each change better targets the job
        • Highlight key skills and experiences emphasized

        2. INTERVIEW PREPARATION ADVICE:
        • Key talking points for the interview
        • How to discuss the highlighted experiences
        • Technical topics to review
        • Potential questions to prepare for
        • STAR method examples for key achievements

        3. NEXT STEPS:
        • Additional skills to develop
        • Certifications to consider
        • Portfolio suggestions
        • Networking recommendations

        FINAL CHECK - VERIFY:
        1. Resume is SPECIFICALLY TAILORED to job description
        2. ALL experience is included but PRIORITIZED for relevance
        3. Skills and technologies MATCH job requirements
        4. NO fictional or assumed information
        5. Original contact details preserved
        6. Both PART 1 and PART 2 included with clear separation

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
        # Create a temporary file with a unique name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='wb') as temp_file:
            temp_path = temp_file.name
            
            # Set up the document with proper margins
            doc = SimpleDocTemplate(
                temp_path,
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
            
            # Build PDF
            doc.build(story)
            
        return temp_path
    except Exception as e:
        print(f"[PDF ERROR] Error creating PDF: {str(e)}")
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise e

def split_ai_response(response):
    """Split OpenAI response into resume and analysis parts"""
    # Find the parts using regex
    resume_match = re.search(r'PART 1:.*?(?=PART 2:|$)', response, re.DOTALL)
    analysis_match = re.search(r'PART 2:.*?(?=FINAL CHECK|$)', response, re.DOTALL)
    
    resume_text = resume_match.group(0) if resume_match else ""
    analysis_text = analysis_match.group(0) if analysis_match else ""
    
    return resume_text.strip(), analysis_text.strip()

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
            "POST /search-similar-jobs": "Search for similar jobs"
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
    temp_pdf_path = None
    try:
        print("\n[Optimize] Starting resume optimization request")
        print(f"[Optimize] Request Content-Type: {request.content_type}")
        print(f"[Optimize] Files in request: {list(request.files.keys())}")
        
        # Check for resume file
        if 'resume' not in request.files:
            print("[Optimize ERROR] No resume file in request")
            return jsonify({
                "success": False,
                "error": "No resume file provided"
            }), 400
            
        resume_file = request.files['resume']
        if resume_file.filename == '':
            print("[Optimize ERROR] Empty filename")
            return jsonify({
                "success": False,
                "error": "No resume file selected"
            }), 400
            
        print(f"[Optimize] Resume file received: {resume_file.filename}")
            
        # Check for job URL
        job_url = request.form.get('job_url')
        if not job_url:
            print("[Optimize ERROR] No job URL provided")
            return jsonify({
                "success": False,
                "error": "Missing job_url in request"
            }), 400
            
        print(f"[Optimize] Job URL received: {job_url}")
        
        # Extract job details from URL
        job_details = extract_job_details(job_url)
        if not job_details:
            raise Exception("Failed to extract job details")

        # Get job details using the LinkedIn scraper
        print("[Optimize] Fetching job details from LinkedIn...")
        scraper = LinkedInJobScraper()
        job_details = scraper.get_job_details(job_url)
        
        if not job_details:
            print("[Optimize ERROR] Failed to get job details")
            return jsonify({
                "success": False,
                "error": "Failed to get job details"
            }), 404
            
        print("[Optimize] Successfully retrieved job details")

        # Extract text from PDF
        print("[Optimize] Starting PDF text extraction...")
        resume_text = extract_text_from_pdf(resume_file)
        print("[Optimize] Successfully extracted text from PDF")
        
        # Prepare prompt for AI model
        print("[Optimize] Preparing prompt for optimization...")
        prompt = f"""You are an expert ATS optimization and career advisor. Analyze this resume for a {job_details['title']} position and provide TWO parts: an optimized resume and a detailed analysis.

        Original Resume:
        {resume_text}

        Job Description:
        {job_details['description']}

        Provide your response in TWO clearly marked sections:

        PART 1: OPTIMIZED RESUME
        =======================
        Create a clean, professional resume with these sections:
        1. Contact Information (keep original details)
        2. Summary (2-3 lines highlighting most relevant qualifications)
        3. Skills (prioritize relevant technical skills)
        4. Experience (emphasize achievements and metrics)
        5. Education (if present in original)

        Format Rules:
        - Remove any "ATS-FRIENDLY" headers or separator lines
        - Use clean, consistent formatting
        - Use bullet points (•) for experience and skills
        - Keep original dates and company names
        - Highlight metrics and achievements

        PART 2: DETAILED ANALYSIS
        =======================

        1. KEY IMPROVEMENTS MADE:
        • List 3-5 specific improvements made to the resume
        • Focus on content reorganization and emphasis
        • Explain how each change improves ATS matching
        • Highlight key skills and experiences emphasized

        2. INTERVIEW PREPARATION ADVICE:
        • Prepare 3-4 STAR stories from your experience
        • Key technical topics to review based on job requirements
        • Suggested responses to common questions
        • Projects or achievements to highlight
        • Questions to ask the interviewer

        3. NEXT STEPS:
        • Skills to develop or strengthen
        • Certifications that would add value
        • Portfolio projects to consider
        • Industry knowledge to research

        IMPORTANT RULES:
        1. MUST provide all three sections in Part 2
        2. Use bullet points (•) for all lists
        3. Be specific and actionable in recommendations
        4. Focus on the job requirements
        5. Maintain all original experience and dates
        6. Both PART 1 and PART 2 included with clear separation

        ‼️ IMPORTANT: Show the COMPLETE response with both parts clearly separated.
        """

        print("[Optimize] Sending request to AI model...")
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Using the original model
            messages=[
                {"role": "system", "content": "You are an expert ATS optimization and career advisor. Provide detailed, specific advice for both resume optimization and interview preparation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        # Split the response into resume and analysis parts
        resume_text, analysis = split_ai_response(response.choices[0].message.content)
        if not resume_text or not analysis:
            raise Exception("Failed to parse AI response")

        # Create PDF from optimized resume text
        print("[Optimize] Creating PDF from optimized resume...")
        pdf_data = create_pdf_from_text(resume_text)
        
        # Get user ID from request headers
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            print("[Optimize ERROR] No user ID provided")
            return jsonify({
                "success": False,
                "error": "User ID is required"
            }), 400

        # Format job title for resume name
        resume_name = job_details['title'].replace(' ', '_').lower()
            
        try:
            # Save the resume first
            resume_data = {
                'user_id': user_id,
                'title': resume_name,
                'optimized_pdf_url': None,  # Will be set when PDF is uploaded
                'analysis': analysis,
                'job_url': job_url,
                'status': 'completed',
                'created_at': 'now()',
                'updated_at': 'now()'
            }

            print(f"[Optimize] Saving resume data: {resume_data}")
            resume_result = supabase.table('resumes').insert(resume_data).execute()
            print(f"[Optimize] Resume save result: {resume_result}")

            if not resume_result.data:
                print("[Optimize ERROR] Failed to save resume")
                raise Exception("Failed to save resume")

            resume_id = resume_result.data[0]['id']
            print(f"[Optimize] Successfully saved resume with ID: {resume_id}")

            # Now save the job with the resume_id
            job_data = {
                'user_id': user_id,
                'resume_id': resume_id,  # Link to the resume we just created
                'company': job_details['company'],
                'job_title': job_details['title'],
                'job_url': job_url,
                'job_description': job_details['description'],
                'status': 'new',
                'created_at': 'now()',
                'updated_at': 'now()'
            }
                
            print(f"[Optimize] Inserting job data: {job_data}")
            result = supabase.table('job_applications').insert(job_data).execute()
                
            if not result.data:
                print("[Optimize ERROR] Failed to save job details")
                raise Exception("Failed to save job details")
                    
            job_id = result.data[0]['id']
            print(f"[Optimize] Successfully saved job with ID: {job_id}")

        except Exception as e:
            print(f"[Optimize ERROR] Database error: {str(e)}")
            return jsonify({
                "success": False,
                "error": f"Failed to save data: {str(e)}"
            }), 500

        # Return the optimized resume and analysis
        try:
            # Read the PDF file into memory
            with open(pdf_data, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                
            # Create JSON response with PDF data and analysis
            response = jsonify({
                "success": True,
                "analysis": analysis,
                "pdf_data": base64.b64encode(pdf_data).decode('utf-8'),
                "job_details": job_details
            })
            
            # Set content type to application/json
            response.headers['Content-Type'] = 'application/json'
            
            print("[Optimize] Sending JSON response with PDF and analysis...")
            return response
        except Exception as e:
            print(f"[Optimize ERROR] Error sending PDF: {str(e)}")
            raise e
        finally:
            # Clean up the temp file
            try:
                if os.path.exists(pdf_data):
                    os.unlink(pdf_data)
            except Exception as e:
                print(f"[Optimize WARNING] Failed to clean up temp file: {str(e)}")
        
    except Exception as e:
        print(f"[Optimize ERROR] Error during optimization: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        # Clean up temporary file
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.unlink(temp_pdf_path)
            except Exception as e:
                print(f"[Optimize WARNING] Failed to clean up temp file: {str(e)}")

@app.route('/api/resumes', methods=['GET', 'OPTIONS'])
def get_resumes():
    """Get all resumes for a user"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        user_id = request.headers.get('X-User-Id')
        limit = request.args.get('limit', type=int)  # Optional limit parameter
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        # Fetch resumes from Supabase
        query = supabase.table('resumes')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)  # Order by newest first
            
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
            .create_signed_url(f"{file_path}", 300)  # URL valid for 5 minutes

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

    if request.method == 'GET':
        return get_jobs()
    elif request.method == 'POST':
        return save_job()

@app.route('/api/jobs/<job_id>/status', methods=['PUT', 'OPTIONS'])
def job_status(job_id):
    """Handle job status endpoint"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-Id')
        response.headers.add('Access-Control-Allow-Methods', 'PUT,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    return update_job_status(job_id)

# Move these to be helper functions
def get_jobs():
    """Get all jobs for a user"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "Missing X-User-Id header"}), 401

        print(f"Getting jobs for user: {user_id}")
        
        # Get jobs from Supabase with resume data
        response = supabase.table('job_applications')\
            .select('*, resume:resumes(id, analysis, title, created_at)')\
            .eq('user_id', user_id)\
            .order('created_at')\
            .execute()

        print(f"Raw response data: {response.data}")

        if not response.data:
            return jsonify([])

        # Transform the response to include resume analysis
        jobs = []
        for job in response.data:
            job_data = {**job}
            if job.get('resume'):
                job_data['analysis'] = job['resume'].get('analysis')
            jobs.append(job_data)

        print(f"Transformed jobs data: {jobs}")
        return jsonify(jobs)
    except Exception as e:
        print(f"Error getting jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500

def save_job():
    """Save a job application"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "Missing X-User-Id header"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400

        required_fields = ['job_title', 'company', 'job_description', 'job_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Get the latest resume for this user
        resume_response = supabase.table('resumes')\
            .select('id')\
            .eq('user_id', user_id)\
            .order('created_at')\
            .limit(1)\
            .execute()

        resume_id = resume_response.data[0]['id'] if resume_response.data else None

        # Save job to Supabase
        job_data = {
            'user_id': user_id,
            'job_title': data['job_title'],
            'company': data['company'],
            'job_description': data['job_description'],
            'job_url': data['job_url'],
            'resume_id': resume_id,
            'status': 'pending'
        }

        response = supabase.table('job_applications')\
            .insert(job_data)\
            .execute()

        if not response.data:
            return jsonify({"error": "Failed to save job"}), 500

        return jsonify(response.data[0])
    except Exception as e:
        print(f"Error saving job: {str(e)}")
        return jsonify({"error": str(e)}), 500

def update_job_status(job_id):
    """Update job application status"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "Missing X-User-Id header"}), 401

        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Missing status in request body"}), 400

        # Verify valid status
        valid_statuses = ['pending', 'applied', 'interviewing', 'offered', 'rejected']
        if data['status'] not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

        # Update job in Supabase
        response = supabase.table('job_applications')\
            .update({'status': data['status']})\
            .eq('id', job_id)\
            .eq('user_id', user_id)\
            .execute()

        if not response.data:
            return jsonify({"error": "Job not found or not authorized"}), 404

        return jsonify(response.data[0])
    except Exception as e:
        print(f"Error updating job status: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
    print("- GET /api/jobs - Get user's job applications")
    print("- POST /api/jobs - Save a job application")
    print("- PUT /api/jobs/<id>/status - Update job application status")
    
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