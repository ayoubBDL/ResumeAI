from dotenv import load_dotenv
import os
from openai import OpenAI
import requests
import json
import io
import base64
import pdfplumber
from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from services.linkedin_batch_scraper import LinkedInJobScraper
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle, HRFlowable
import re
import tempfile
import time

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
client = OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
        
        response = client.chat.completions.create(
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
        """

        print("[Optimize] Sending request to AI model...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert ATS optimization and career advisor. Provide detailed, specific advice for both resume optimization and interview preparation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2500
        )

        # Extract the response
        ai_response = response.choices[0].message.content.strip()
        
        # Split the response into resume and analysis parts using the correct marker
        parts = ai_response.split("PART 2: DETAILED ANALYSIS")
        optimized_resume = parts[0].split("PART 1: OPTIMIZED RESUME")[-1].strip() if len(parts) > 0 else ""
        analysis = parts[1].strip() if len(parts) > 1 else ""
        
        print("[DEBUG] Analysis extracted:", analysis)
        
        # Create the response object
        response_data = {
            "optimized_resume": optimized_resume,
            "analysis": analysis
        }

        print("[DEBUG] Final response data:", response_data)
        
        # Generate PDF from resume text
        print("[Optimize] Generating optimized resume PDF...")
        temp_pdf_path = create_pdf_from_text(optimized_resume)
        
        try:
            # Read the PDF file into memory
            with open(temp_pdf_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                
            # Create JSON response with PDF data and analysis
            response = jsonify({
                "success": True,
                "analysis": analysis,
                "pdf_data": base64.b64encode(pdf_data).decode('utf-8')
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
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
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

@app.route('/upload', methods=['POST'])
def upload_file():
    # Remove the delete endpoint since we're handling it in the frontend
    pass

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
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"\nServer Configuration:")
    print(f"- Host: {host}")
    print(f"- Port: {port}")
    print(f"- Debug Mode: {debug}")
    
    print("\nAvailable Endpoints:")
    print("- GET / - API information")
    print("- GET /health - Health check")
    print("- POST /get-job-details - Get job details from LinkedIn")
    print("- POST /optimize - Optimize resume for job")
    print("- POST /scrape-jobs - Scrape jobs from LinkedIn")
    print("- POST /scrape-job-url - Scrape job by URL")
    print("- POST /search-similar-jobs - Search for similar jobs")
    
    print(f"\nServer running at http://{host}:{port}")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(f"\nError starting server: {str(e)}")
        return

if __name__ == '__main__':
    print("Starting Resume Optimizer Server...")
    print("Available endpoints:")
    print("  POST /get-job-details - Get job details from LinkedIn")
    print("  POST /optimize - Optimize resume")
    print("  POST /scrape-jobs - Scrape jobs from LinkedIn")
    print("  POST /scrape-job-url - Scrape job by URL")
    print("  POST /search-similar-jobs - Search for similar jobs")
    app.run(host='localhost', port=5050)