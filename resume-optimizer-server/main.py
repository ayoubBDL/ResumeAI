from flask import Flask, request, jsonify
from flask_cors import CORS
from services.linkedin_scraper import LinkedInJobScraper
import requests
from dotenv import load_dotenv
import os
import PyPDF2
import io

# Load environment variables
load_dotenv()

OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama API URL

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def extract_text_from_pdf(pdf_file):
    try:
        # Read PDF file
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        raise Exception("Could not read PDF file. Please make sure it's a valid PDF.")

def generate_with_ollama(prompt, system_prompt=""):
    try:
        # response = requests.post(
        #     f"{OLLAMA_BASE_URL}/api/generate",
        #     json={
        #         "model": "llama3.1",  # or any other model you have pulled
        #         "prompt": prompt,
        #         "system": system_prompt,
        #         "stream": False
        #     }
        # )
        # response.raise_for_status()
        # return response.json()["response"]
        return prompt;
    except Exception as e:
        print(f"Ollama API error: {str(e)}")
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
            "GET /test": "Test LinkedIn API connection",
            "POST /optimize": "Optimize resume for job posting"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

@app.route('/test')
def test():
    try:
        scraper = LinkedInJobScraper()
        job_url = "https://www.linkedin.com/jobs/view/4120998628"
        job_details = scraper.get_job_details(job_url)
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

@app.route('/optimize', methods=['POST'])
def optimize_resume():
    try:
        print("Request Content-Type:", request.content_type)
        print("Request form:", request.form)
        print("Request files:", request.files)
        print("Request json:", request.get_json(silent=True))

        # Handle both JSON and form-data
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "error": "No JSON data provided"
                }), 400
            
            resume_text = data.get('resume')
            job_url = data.get('jobUrl')
            
            if not resume_text or not job_url:
                return jsonify({
                    "success": False,
                    "error": "Missing resume text or job URL"
                }), 400
                
        else:  # Handle multipart/form-data
            if 'resume' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "No resume file provided"
                }), 400
                
            resume_file = request.files['resume']
            job_url = request.form.get('jobUrl')
            
            if not resume_file or not job_url:
                return jsonify({
                    "success": False,
                    "error": "Missing resume file or job URL"
                }), 400
                
            if resume_file.filename.lower().endswith('.pdf'):
                # Convert PDF to text
                resume_text = extract_text_from_pdf(resume_file)
            else:
                # Assume it's text
                resume_text = resume_file.read().decode('utf-8')

        print(f"Job URL: {job_url}")
        print(f"Resume text length: {len(resume_text)} characters")
        
        # Get job details
        scraper = LinkedInJobScraper()
        job_details = scraper.get_job_details(job_url)
        print(f"Got job details for: {job_details.get('title', 'Unknown position')}")
        
        # Prepare prompt for optimization
        optimize_prompt = f"""
        Job Description:
        Title: {job_details['title']}
        Company: {job_details['company']}
        Description: {job_details['description']}

        Original Resume:
        {resume_text}

        Please optimize this resume for the job description above. Follow these instructions:
        1. Match keywords and technical skills from the job description
        2. Highlight relevant experience that aligns with the job requirements
        3. Quantify achievements where possible
        4. Use active voice and impactful verbs
        5. Keep the same format as the original resume
        6. Return only the optimized resume text, no explanations

        Optimized Resume:
        """
        
        # Get optimized resume using Ollama
        optimized_resume = generate_with_ollama(
            optimize_prompt,
            "You are a professional resume writer and career coach."
        )
        
        # Create ATS format prompt
        ats_prompt = f"""
        Convert this resume into an ATS-friendly format following these rules:
        1. Use a clean, simple format with no fancy formatting
        2. Include clear section headers (Summary, Experience, Education, Skills)
        3. Remove any graphics, tables, columns, or special characters
        4. Use standard bullet points (•)
        5. Use common section titles that ATS systems recognize
        6. Include all relevant keywords from the job description
        7. Use a chronological format
        8. Return only the ATS-formatted resume, no explanations

        Resume to convert:
        {optimized_resume}
        
        ATS-Friendly Format:
        """
        
        # Get ATS version using Ollama
        ats_resume = generate_with_ollama(
            ats_prompt,
            "You are an ATS optimization expert."
        )
        
        print("Resume optimization complete!")
        
        return jsonify({
            "success": True,
            "data": {
                "originalResume": resume_text,
                "optimizedResume": optimized_resume,
                "atsResume": ats_resume,
                "jobDetails": job_details
            }
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
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
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"\nServer Configuration:")
    print(f"- Host: {host}")
    print(f"- Port: {port}")
    print(f"- Debug Mode: {debug}")
    
    print("\nAvailable Endpoints:")
    print("- GET / - API information")
    print("- GET /health - Health check")
    print("- GET /test - Test LinkedIn API")
    print("- POST /optimize - Optimize resume for job")
    
    print(f"\nServer running at http://{host}:{port}")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(f"\nError starting server: {str(e)}")
        return

if __name__ == '__main__':
    print("Starting Resume Optimizer Server...")
    print("Available endpoints:")
    print("  GET  /test     - Test LinkedIn API")
    print("  POST /optimize - Optimize resume")
    app.run(host='localhost', port=5050)