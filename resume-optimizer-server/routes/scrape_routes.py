from flask import Blueprint, request, jsonify
from services.linkedin_batch_scraper import LinkedInJobScraper

# Create a Blueprint for scrape routes
scrape_routes = Blueprint('scrape_routes', __name__)

@scrape_routes.route('/scrape-jobs', methods=['POST'])
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

@scrape_routes.route('/scrape-job-url', methods=['POST'])
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
