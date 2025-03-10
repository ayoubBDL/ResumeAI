import requests
import re
import os
from typing import Dict
from dotenv import load_dotenv
import sys
from bs4 import BeautifulSoup

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

    def extract_job_details(self, job_url):
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

    def get_job_details(self, url):
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
