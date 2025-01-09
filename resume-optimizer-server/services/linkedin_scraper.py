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
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        log(f"LinkedIn scraper initialized with client_id: {self.client_id}")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("LinkedIn API credentials not found in .env file")

    def extract_job_id(self, url: str) -> str:
        """Extract job ID from LinkedIn job URL"""
        log(f"Extracting job ID from URL: {url}")
        match = re.search(r'view/(\d+)', url)
        if not match:
            raise ValueError("Invalid LinkedIn job URL format")
        job_id = match.group(1)
        log(f"Extracted job ID: {job_id}")
        return job_id

    def get_access_token(self) -> str:
        """Get LinkedIn API access token"""
        log("Getting LinkedIn API access token...")
        url = 'https://www.linkedin.com/oauth/v2/accessToken'
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        log(f"Making request to {url}")
        response = requests.post(url, data=data)
        log(f"Response status: {response.status_code}")
        log(f"Response body: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.text}")
        
        token_data = response.json()
        log("Successfully got access token")
        return token_data['access_token']

    def get_job_details(self, url: str) -> Dict:
        """Get job details from LinkedIn API"""
        try:
            log(f"\n=== Getting job details for URL: {url} ===")
            
            # Extract job ID
            job_id = self.extract_job_id(url)
            
            # Get access token
            access_token = self.get_access_token()
            log("Got access token, making API request...")
            
            # Make API request for job details
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            api_url = f'https://api.linkedin.com/v2/jobs/{job_id}'
            log(f"Making request to {api_url}")
            
            response = requests.get(api_url, headers=headers)
            log(f"Response status: {response.status_code}")
            log(f"Response body: {response.text}")
            
            if response.status_code != 200:
                raise Exception(f"Failed to get job details: {response.text}")
            
            data = response.json()
            log("Successfully got job details")
            
            # Extract and return relevant job details
            result = {
                'title': data.get('title', ''),
                'company': data.get('companyName', ''),
                'location': data.get('formattedLocation', ''),
                'description': data.get('description', {}).get('text', ''),
                'employmentType': data.get('employmentStatus', ''),
                'industries': data.get('industries', []),
                'postedAt': data.get('postingTimestamp')
            }
            log(f"Extracted job details: {result}")
            return result
            
        except Exception as e:
            log(f"Error getting job details: {str(e)}")
            import traceback
            log(f"Traceback: {traceback.format_exc()}")
            raise
