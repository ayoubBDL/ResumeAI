import requests
import re
import os
from typing import Dict
from dotenv import load_dotenv
import sys

def log(msg):
    print(msg, file=sys.stderr, flush=True)

load_dotenv()

class LinkedInJobScraper:
    def __init__(self):
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        log("LinkedIn scraper initialized")
        
        if not self.access_token:
            raise ValueError("LinkedIn access token not found in .env file")

    def extract_job_id(self, url: str) -> str:
        """Extract job ID from LinkedIn job URL"""
        log(f"Extracting job ID from URL: {url}")
        match = re.search(r'view/(\d+)', url)
        if not match:
            raise ValueError("Invalid LinkedIn job URL format")
        job_id = match.group(1)
        log(f"Extracted job ID: {job_id}")
        return job_id

    def get_job_details(self, url: str) -> Dict:
        """Get job details using LinkedIn API"""
        try:
            log(f"\n=== Getting job details for URL: {url} ===")
            
            # Extract job ID
            job_id = self.extract_job_id(url)
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0',
                'LinkedIn-Version': '202304'
            }
            
            # Use the Jobs API with the correct endpoint
            api_url = 'https://api.linkedin.com/v2/jobs'
            params = {
                'decorationId': 'com.linkedin.voyager.deco.jobs.web.shared.WebLightJobPosting-23',
                'ids': job_id
            }
            
            log(f"Making request to {api_url} with params {params}")
            response = requests.get(api_url, headers=headers, params=params)
            log(f"Response status: {response.status_code}")
            log(f"Response body: {response.text}")
            
            if response.status_code != 200:
                # Try alternative API endpoint
                api_url = f'https://api.linkedin.com/rest/jobs/{job_id}'
                log(f"Trying alternative endpoint: {api_url}")
                response = requests.get(api_url, headers=headers)
                log(f"Response status: {response.status_code}")
                log(f"Response body: {response.text}")
                
                if response.status_code != 200:
                    raise Exception(f"Failed to get job details: {response.text}")
            
            data = response.json()
            log("Successfully got job details")
            
            # Extract job details from response
            job_data = data.get('elements', [{}])[0] if 'elements' in data else data
            
            result = {
                'title': job_data.get('title', ''),
                'company': job_data.get('companyName', '') or job_data.get('company', {}).get('name', ''),
                'location': job_data.get('formattedLocation', '') or job_data.get('location', ''),
                'description': (
                    job_data.get('description', {}).get('text', '') or 
                    job_data.get('description', '') or 
                    job_data.get('jobDescription', '')
                ),
                'employmentType': job_data.get('employmentStatus', '') or job_data.get('employmentType', ''),
                'industries': job_data.get('industries', []),
                'url': url
            }
            
            log(f"Extracted job details: {result}")
            return result
            
        except Exception as e:
            log(f"Error getting job details: {str(e)}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")
            raise
