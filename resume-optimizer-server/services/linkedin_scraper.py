from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

class LinkedInScraper:
    def __init__(self):
        self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    async def scrape_job(self, url: str) -> dict:
        try:
            self.driver.get(url)
            time.sleep(2)  # Allow page to load

            # Wait for job details to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title"))
            )

            # Extract job information
            job_data = {
                "title": self.driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title").text.strip(),
                "company": self.driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name").text.strip(),
                "location": self.driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__bullet").text.strip(),
                "description": self.driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-description").text.strip(),
            }

            # Extract requirements if available
            try:
                requirements = self.driver.find_elements(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-requirements li")
                job_data["requirements"] = [req.text.strip() for req in requirements]
            except:
                job_data["requirements"] = []

            return job_data

        except Exception as e:
            raise Exception(f"Failed to scrape LinkedIn job: {str(e)}")

        finally:
            self.driver.quit()

    def __del__(self):
        try:
            self.driver.quit()
        except:
            pass
