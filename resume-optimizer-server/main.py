import sys
from dotenv import load_dotenv
import os
import openai
import requests
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from waitress import serve
from supabase import create_client, Client
from loguru import logger
import sentry_sdk
# Import route blueprints
from routes.job_routes import job_routes
from routes.user_routes import user_routes
from routes.health_routes import health_routes
from routes.scrape_routes import scrape_routes
from routes.resume_routes import resume_routes
from routes.subscription_routes import subscription_routes
from routes.optimize_routes import optimize_routes

# Load environment variables
load_dotenv()

# Configure Loguru for production
logger.add("app.log", rotation="10 MB", level="ERROR")  # Log errors to a file
logger.add(sys.stdout, level="ERROR")  

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)
# Validate and set OpenAI API key
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

# Validate PayPal configuration
if not os.getenv('PAYPAL_API_URL'):
    raise ValueError("PayPal API URL not found in environment variables")

# Initialize Flask app
app = Flask(__name__)

# Define allowed origins
ALLOWED_ORIGINS = [
    os.getenv('CLIENT_URL', 'https://jobsageai.netlify.app'),
    'http://localhost:5173',
    # Add any additional development/staging URLs as needed
]

# Configure CORS
CORS(app, resources={
    r"/*": {  # Apply to all routes
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "X-User-Id",
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Methods"
        ],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"],
        "max_age": 600,
        "vary_header": True
    }
})

# Register blueprints
app.register_blueprint(job_routes)
app.register_blueprint(user_routes)
app.register_blueprint(health_routes)
app.register_blueprint(scrape_routes)
app.register_blueprint(optimize_routes)
app.register_blueprint(subscription_routes)
app.register_blueprint(resume_routes)

# Development configuration
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

# CORS middleware
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin and origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-User-Id'
    return response

# Global error handler
@app.errorhandler(Exception)
def handle_exception(e):
    # Extract user ID from request headers
    user_id = request.headers.get('X-User-Id', 'Unknown User')  # Default to 'Unknown User' if not present

    # Construct the full request URL
    full_url = request.url
    query_params = request.query_string.decode()  # Get query parameters as a string

    # Log the error with additional context
    logger.error(
        f"An error occurred: {str(e)} and user_id: {user_id} and full_url: {full_url} and query_params: {query_params}",
        exc_info=True,  # Include the full traceback
        extra={
            "request_method": request.method,
            "request_path": request.path,
            "full_url": full_url,  # Log the full URL
            "query_params": query_params,  # Log the query parameters
            "request_headers": dict(request.headers),
            "request_body": request.get_json(silent=True) or request.form or request.data,
            "user_id": user_id  # Log the user ID
        },
    )
    sentry_sdk.capture_exception(e)
    
    # Return a JSON response with the error message
    return jsonify({"success": False, "error": str(e), "user_id": user_id}), 500

@app.route('/')
def home():
    """Root endpoint providing API information"""
    return jsonify({
        "message": "Hello World",
        "status": "healthy",
    })

def validate_environment():
    """Validate required environment variables"""
    required_vars = [
        'OPENAI_API_KEY',  # OpenAI API key
        'SUPABASE_URL',     # Supabase project URL
        'SUPABASE_KEY',     # Supabase API key
        'PAYPAL_API_URL',   # PayPal API URL
        'CLIENT_URL',   
        'SENTRY_DSN'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"- {var}")
        return False
    
    logger.info("All required environment variables are set.")
    return True

# Main application entry point
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
    
    # Print configuration
    print(f"\nServer Configuration:")
    print(f"- Host: {host}")
    print(f"- Port: {port}")
    print(f"- Debug Mode: {debug}")
    print(f"- Allowed Origins: {ALLOWED_ORIGINS}")
    print(f"- Client URL: {os.getenv('CLIENT_URL')}")

    # Run server
    if debug:
        # Development mode
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            threaded=True
        )
    else:
        # Production mode with Waitress
        print("\nRunning in production mode with Waitress...")
        logger.info("Resume Optimizer API is running")
        serve(app, host=host, port=port)

if __name__ == '__main__':
    main()