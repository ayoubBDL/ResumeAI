from typing import Dict
import re
from bs4 import BeautifulSoup
import requests

class LinkedInJobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def extract_job_id(self, url: str) -> str:
        """Extract job ID from LinkedIn job URL"""
        match = re.search(r'view/(\d+)', url)
        if not match:
            raise ValueError("Invalid LinkedIn job URL format")
        return match.group(1)

    def get_job_details(self, job_url: str) -> Dict:
        """Get job details using job URL"""
        try:
            # Extract job ID from URL
            job_id = self.extract_job_id(job_url)
            
            # Get job details
            url = f'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                print(f"Failed to get job details: Status code {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract job details
            title = soup.find('h1', {'class': 'top-card-layout__title'})
            company = soup.find('a', {'class': 'topcard__org-name-link'})
            location = soup.find('span', {'class': 'topcard__flavor--bullet'})
            description = soup.find('div', {'class': 'description__text'})
            
            job_details = {
                'title': title.text.strip() if title else '',
                'company': company.text.strip() if company else '',
                'location': location.text.strip() if location else '',
                'description': description.text.strip() if description else '',
                'job_url': job_url
            }
            
            return job_details
            
        except Exception as e:
            print(f"Error getting job details: {str(e)}")
            return None
