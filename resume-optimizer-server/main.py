from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
import time
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class LinkedInJobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def validate_linkedin_url(self, url):
        """Validate if the URL is a LinkedIn job posting URL"""
        parsed = urlparse(url)
        if not parsed.netloc.endswith('linkedin.com'):
            raise ValueError("Not a valid LinkedIn URL")
        if '/jobs/view/' not in url:
            raise ValueError("Not a valid LinkedIn job posting URL")
        return True

    def get_job_details(self, url, max_retries=3):
        """Get job details with retry mechanism and proper error handling"""
        try:
            self.validate_linkedin_url(url)
            
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        job_title = self._safe_extract(soup, "h1", {"class": "top-card-layout__title"})
                        company = self._safe_extract(soup, "a", {"class": "topcard__org-name-link"})
                        description = self._safe_extract(soup, "div", {"class": "show-more-less-html__markup"})
                        
                        if not description:
                            description = self._safe_extract(soup, "div", {"class": "description__text"})
                        
                        if not any([job_title, company, description]):
                            raise ValueError("Could not extract job details")
                        
                        return {
                            "title": job_title,
                            "company": company,
                            "description": description,
                            "url": url
                        }
                    
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2 ** attempt)
                    continue
                    
        except Exception as e:
            raise Exception(f"Failed to scrape job details: {str(e)}")

    def _safe_extract(self, soup, tag, attrs):
        """Safely extract text from BeautifulSoup object"""
        element = soup.find(tag, attrs)
        return element.get_text(strip=True) if element else ""

# Initialize Flask
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    """Root endpoint providing API information"""
    return jsonify({
        "message": "Resume Optimizer API is running",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "API information",
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
    """Test endpoint for LinkedIn scraping"""
    try:
        scraper = LinkedInJobScraper()
        job_url = request.args.get('url', "https://www.linkedin.com/jobs/view/3754954736")
        
        job_details = scraper.get_job_details(job_url)
        
        if not job_details.get('description'):
            return jsonify({
                "success": False,
                "error": "Could not fetch job details"
            }), 400
            
        return jsonify({
            "success": True,
            "data": job_details
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/optimize', methods=['POST'])
def optimize():
    """Endpoint to optimize resume based on job posting"""
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400

        job_url = data.get('job_url')
        resume_text = data.get('resume')
        
        if not job_url or not resume_text:
            return jsonify({
                "success": False,
                "error": "Missing required fields: job_url or resume"
            }), 400
        
        # Get job details
        scraper = LinkedInJobScraper()
        job_details = scraper.get_job_details(job_url)
        
        # Prepare prompt for GPT
        prompt = f"""
        Job Description:
        {job_details['description']}
        
        Original Resume:
        {resume_text}
        
        Please optimize this resume for the job description above. Focus on:
        1. Matching keywords and skills
        2. Highlighting relevant experience
        3. Quantifying achievements
        4. Using active voice and impactful verbs
        5. Maintaining truthfulness - do not invent experiences
        
        Format the response as a properly formatted resume.
        """
        
        # Call OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional resume writer and career coach."},
                {"role": "user", "content": prompt}
            ]
        )
        
        optimized_resume = completion.choices[0].message.content
        
        return jsonify({
            "success": True,
            "data": {
                "original_resume": resume_text,
                "optimized_resume": optimized_resume,
                "job_details": job_details
            }
        })
        
    except Exception as e:
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
    port = int(os.getenv('PORT', 3000))
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
    main()