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
from routes.job_routes import job_routes  # Import the job routes
from routes.user_routes import user_routes  # Import user routes
from routes.health_routes import health_routes  # Import health routes
from routes.scrape_routes import scrape_routes  # Import scrape routes
from routes.resume_routes import resume_routes  # Import resume routes
from routes.subscription_routes import subscription_routes
from routes.optimize_routes import optimize_routes

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

app.register_blueprint(job_routes)
app.register_blueprint(user_routes)  # No prefix needed for user routes
app.register_blueprint(health_routes)  # No prefix needed for health routes
app.register_blueprint(scrape_routes)  # No prefix needed for scrape routes
app.register_blueprint(optimize_routes)  # No prefix needed for optimize routes
app.register_blueprint(subscription_routes)
app.register_blueprint(resume_routes)

# Define allowed origins
ALLOWED_ORIGINS = [
    os.getenv('CLIENT_URL', 'https://jobsageai.netlify.app'),
    'http://localhost:5173',
]

# Centralized CORS configuration
CORS(app, resources={r"/api/*": {
    "origins": ALLOWED_ORIGINS,
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-User-Id"],
    "supports_credentials": True,
    "expose_headers": ["Content-Type", "Authorization"],
    "max_age": 600
}})

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