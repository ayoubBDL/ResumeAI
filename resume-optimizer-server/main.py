from dotenv import load_dotenv
import os
from openai import OpenAI
import requests
import json
import io
import pdfplumber
from flask import Flask, request, jsonify, send_file
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
import base64

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
                {"role": "system", "content": """You are a professional career advisor that helps optimize resumes and prepare candidates for job opportunities. Your task is to provide a comprehensive analysis in these key areas:

1. Resume Optimization:
   - Identify key skills and experience gaps
   - Suggest specific modifications to match job requirements
   - Add relevant technical keywords and industry terms
   - Improve quantifiable achievements

2. Technical Interview Preparation:
   - List specific technical topics to study based on job requirements
   - Provide example technical questions and suggested answers
   - Recommend coding challenges related to the role's tech stack
   - Suggest system design scenarios to practice
   - Include relevant documentation and resources to review

3. Behavioral Interview Preparation:
   - Prepare STAR format responses using the candidate's experience
   - Suggest specific projects to highlight during interviews
   - Provide example behavioral questions and how to answer them
   - Include leadership and team collaboration scenarios
   - Recommend ways to discuss challenges and solutions

4. Company Research and Culture Fit:
   - Highlight industry trends relevant to the role
   - Suggest questions to ask interviewers
   - Identify company values and how to demonstrate alignment
   - Research points about company technology and projects
   - Tips for discussing career growth and goals

5. Practical Preparation Steps:
   - Create a study timeline with specific topics
   - List tools and technologies to practice
   - Suggest mock interview exercises
   - Recommend portfolio projects to build
   - Provide resources for further learning

Format the response to focus on ACTIONABLE preparation steps. Each suggestion should be specific and tied to the job requirements. Include example questions, scenarios, and concrete study materials."""},
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
                spaceBefore=16,
                spaceAfter=12,
                textColor=colors.HexColor('#2C3E50'),
                fontName='Helvetica-Bold',
                borderPadding=(0, 0, 8, 0),  # bottom padding for underline
            ))
            
            # Normal text style
            styles.add(ParagraphStyle(
                name='NormalText',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=8,
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
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Remove markers and clean up the text
                line = re.sub(r'^PART \d+:', '', line)  # Remove "PART X:" headers
                line = re.sub(r'\*\*|\#\#', '', line)   # Remove ** and ## markers
                line = line.strip()
                if not line:
                    continue
                
                # Handle different sections
                if "CONTACT SECTION" in line.upper():
                    in_contact_section = True
                    story.append(Spacer(1, 20))
                    continue
                elif "PROFESSIONAL SUMMARY" in line.upper():
                    in_contact_section = False
                    # Add a divider
                    story.append(HRFlowable(
                        width="100%",
                        thickness=1,
                        color=colors.HexColor('#BDC3C7'),
                        spaceBefore=8,
                        spaceAfter=8
                    ))
                    story.append(Paragraph(line.title(), styles['SectionHeading']))
                elif "PROFESSIONAL EXPERIENCE" in line.upper() or "EDUCATION" in line.upper() or "SKILLS" in line.upper():
                    # Add a divider before new main sections
                    story.append(HRFlowable(
                        width="100%",
                        thickness=1,
                        color=colors.HexColor('#BDC3C7'),
                        spaceBefore=8,
                        spaceAfter=8
                    ))
                    story.append(Paragraph(line.title(), styles['SectionHeading']))
                elif in_contact_section:
                    # Special handling for contact section
                    if ":" in line:
                        label, value = line.split(":", 1)
                        story.append(Paragraph(
                            f'<b>{label.strip()}:</b> {value.strip()}',
                            styles['ContactInfo']
                        ))
                    else:
                        # Assume it's the name if it's the first line of contact
                        if not story:  # If this is the very first line
                            story.append(Paragraph(line, styles['Name']))
                        else:
                            story.append(Paragraph(line, styles['ContactInfo']))
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
                            spaceBefore=6,
                            spaceAfter=6
                        ))
                        current_section = []
                    story.append(Paragraph(line, styles['NormalText']))
            
            # Add any remaining bullet points
            if current_section:
                story.append(ListFlowable(
                    [ListItem(Paragraph(item, styles['NormalText'])) for item in current_section],
                    bulletType='bullet',
                    leftIndent=20,
                    spaceBefore=6,
                    spaceAfter=6
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
        prompt = f"""You are a professional career advisor that helps optimize resumes and prepare candidates for job opportunities. Your task is to create an ATS-friendly resume that SPECIFICALLY targets this job position.

        CRITICAL - ABSOLUTELY REQUIRED RULES:
        1. JOB MATCHING (HIGHEST PRIORITY):
           ‼️ Analyze the job description thoroughly
           ‼️ Identify key requirements, skills, and qualifications
           ‼️ Reorganize and emphasize resume content to match job requirements
           ‼️ Use similar terminology as the job description
           ‼️ Highlight experiences that directly relate to job requirements
           ‼️ Ensure technical skills match what's asked in the job

        2. PROFESSIONAL EXPERIENCE:
           ‼️ Look for the "PROFESSIONAL EXPERIENCE" or "WORK EXPERIENCE" section
           ‼️ For each position, include and ADAPT:
              - Exact company name and job title
              - Exact dates
              - Responsibilities that align with job requirements
              - Achievements relevant to the target position
              - Tools and technologies that match job needs
           ‼️ Emphasize experiences that match job requirements
           ‼️ Use action verbs and metrics from original resume

        3. TECHNICAL SKILLS:
           ‼️ Prioritize skills mentioned in job description
           ‼️ Match terminology with job requirements
           ‼️ Group skills by relevance to the position
           ‼️ Keep all original skills but highlight matching ones

        4. PROJECTS:
           ‼️ Prioritize projects using similar technologies
           ‼️ Emphasize projects relevant to job requirements
           ‼️ Keep technical details that align with position

        5. CONTACT AND EDUCATION:
           ‼️ Keep all contact information exactly as in resume
           ‼️ Include education details unchanged
           ‼️ Never modify or assume contact details

        Job Description to Target:
        {job_details['description']}
        
        Original Resume:
        {resume_text}
        
        Your response MUST include BOTH parts:

        PART 1: ATS-FRIENDLY RESUME TARGETING THIS POSITION
        ===================================================
        1. CONTACT SECTION:
           - Only information from original resume
           - Clean, professional format

        2. PROFESSIONAL SUMMARY:
           - Tailored to job requirements
           - Highlight matching qualifications
           - Focus on relevant experience

        3. PROFESSIONAL EXPERIENCE:
           - Prioritize experiences matching job needs
           - Use relevant achievements and metrics
           - Emphasize matching skills and tools
           - Keep all positions but focus on relevant details

        4. TECHNICAL SKILLS:
           - Prioritize skills mentioned in job
           - Group by relevance to position
           - Match job description terminology

        5. PROJECTS:
           - Highlight relevant projects first
           - Emphasize matching technologies
           - Focus on relevant outcomes

        6. EDUCATION:
           - Keep as in original

        FORMAT REQUIREMENTS:
        - ATS-friendly format
        - Clear section headers
        - Bullet points (•)
        - Consistent spacing
        - No tables or columns

        PART 2: OPTIMIZATION ANALYSIS
        ============================
        1. MATCH ANALYSIS:
           - Key job requirements and how resume matches
           - Critical skills alignment
           - Experience relevance
           - Technical skills match

        2. IMPROVEMENT SUGGESTIONS:
           - Skills to emphasize
           - Experiences to highlight
           - Keywords to add
           - Areas to strengthen

        FINAL CHECK - VERIFY:
        1. Resume is SPECIFICALLY TAILORED to job description
        2. ALL experience is included but PRIORITIZED for relevance
        3. Skills and technologies MATCH job requirements
        4. NO fictional or assumed information
        5. Original contact details preserved
        6. Both PART 1 and PART 2 included

        ‼️ IMPORTANT: Show the COMPLETE response, not just a preview. Include both PART 1 and PART 2 in full.
        """
        
        # Generate optimization suggestions using selected model
        print(f"[Optimize] Generating suggestions using OpenAI...")
        suggestions = generate_with_openai(prompt)
        
        # Split response into resume and analysis
        resume_text, analysis_text = split_ai_response(suggestions)
        
        # Generate PDF from resume text
        print("[Optimize] Generating optimized resume PDF...")
        temp_pdf_path = create_pdf_from_text(resume_text)
        
        try:
            # Read the PDF file into memory
            with open(temp_pdf_path, 'rb') as pdf_file:
                pdf_data = pdf_file.read()
                
            # Create response with PDF data
            response = send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"optimized_{resume_file.filename}"
            )
            
            # Set content disposition and type
            response.headers['Content-Disposition'] = f'attachment; filename="optimized_{resume_file.filename}"'
            response.headers['Content-Type'] = 'application/pdf'
            
            print("[Optimize] Sending PDF response...")
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