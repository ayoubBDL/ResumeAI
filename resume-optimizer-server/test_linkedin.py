from services.linkedin_scraper import LinkedInJobScraper

print("\n=== Starting LinkedIn API Test ===")

try:
    print("Creating LinkedIn scraper...")
    scraper = LinkedInJobScraper()
    
    job_url = "https://www.linkedin.com/jobs/view/3754954736"
    print(f"\nTesting with URL: {job_url}")
    
    print("\nGetting job details...")
    job_details = scraper.get_job_details(job_url)
    
    print("\nJob Details:")
    print("-" * 50)
    for key, value in job_details.items():
        print(f"{key}: {value}")
    print("-" * 50)
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    print("\nFull traceback:")
    print(traceback.format_exc())
