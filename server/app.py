import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoverLetterGenerator:
    def __init__(self, resume_text, openai_api_key):
        self.resume = resume_text
        self.openai_api_key = openai_api_key
        
        # Set up Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-notifications')
        # chrome_options.add_argument('--headless')  # Uncomment for headless mode
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def extract_page_content(self, html_content):
        """Extract precise job description content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for unwanted in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            unwanted.decompose()

        # Job description specific selectors for different platforms
        job_description_selectors = [
            # LinkedIn
            '.jobs-description-content__text',
            '.description__text',
            
            # Greenhouse
            '.greenhouse-job-description',
            '.job-description',
            
            # ClimateBase
            '.job-details',
            
            # Ashby
            '.job-description-section',
            
            # Generic fallback selectors
            '#job-description',
            '.job-description',
            '[data-testid="job-description"]'
        ]

        # Try specific selectors first
        for selector in job_description_selectors:
            description_element = soup.select_one(selector)
            if description_element:
                # Extract text, removing extra whitespace
                paragraphs = description_element.find_all(['p', 'li'])
                focused_content = ' '.join([
                    p.get_text(strip=True) 
                    for p in paragraphs 
                    if len(p.get_text(strip=True).split()) > 5  # Only keep paragraphs with substance
                ])
                
                return focused_content[:1500]  # Limit to ~1500 characters
        
        # Fallback: Extract main content areas
        main_content_selectors = [
            'main', 
            'article', 
            'div[class*="content"]', 
            'div[class*="description"]'
        ]
        
        for selector in main_content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                text_content = ' '.join(content_element.get_text(strip=True).split())
                return text_content[:1000]
        
        # Ultimate fallback
        return ' '.join(soup.get_text(strip=True).split())[:800]

    def scrape_job_content(self, url):
        """Enhanced job content scraping with platform-specific handling"""
        try:
            self.driver.get(url)
            time.sleep(3)  # Allow page to load
            
            # Platform-specific preprocessing for known sites
            if 'linkedin.com' in url:
                # Scroll to expand full description
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
            elif 'greenhouse.io' in url:
                # Click "Show more" if exists
                try:
                    show_more = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Show more')]")
                    if show_more:
                        show_more[0].click()
                        time.sleep(1)
                except:
                    pass
            
            # Get the page source after JavaScript rendering
            page_source = self.driver.page_source
            
            # Extract text content
            text_content = self.extract_page_content(page_source)
            
            # Final fallback
            if not text_content:
                text_content = self.driver.find_element(By.TAG_NAME, 'body').text
            
            logger.info(f"Successfully scraped content from: {url}")
            return text_content.strip()

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return "Error scraping job content"

    def generate_multiple_cover_letters(self, job_contents_list):
        """Generate multiple cover letters in a single API request"""
        try:
            logger.info(f"Preparing to generate {len(job_contents_list)} cover letters")
            
            # Prepare resume and job contents
            resume_text = str(self.resume)[:1000]  # Limit resume context
            
            # Construct prompt with focused guidance
            prompt = f"""
            You are an expert career coach creating tailored cover letters.

            Key Instructions:
            - Extract ONLY the most relevant job requirements and responsibilities
            - Focus on 3-4 core job attributes
            - Highlight SPECIFIC matching skills from the resume
            - Use a professional, concise tone
            - Maximum 300 words per cover letter

            Resume Highlights:
            {resume_text}

            Job Postings (Focus on Key Requirements):
            {"\n\n".join([f"### JOB POSTING {i+1} ###\n{content[:1000]}" for i, content in enumerate(job_contents_list)])}

            For each job, create a cover letter that directly addresses:
            1. Why you're an exceptional fit
            2. Specific skills matching job needs
            3. Enthusiasm for the role/company

            Format each cover letter with the marker:
            ### COVER LETTER FOR JOB {1..n} ###
            [Cover letter content]
            """

            # Prepare API request
            api_data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a professional, precise cover letter writer."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 3000
            }

            logger.info("Sending API request")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                },
                json=api_data,
                timeout=45
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse response
            full_response = response.json()['choices'][0]['message']['content'].strip()
            
            # Extract individual cover letters
            cover_letters = []
            for i in range(len(job_contents_list)):
                current_marker = f"### COVER LETTER FOR JOB {i+1} ###"
                next_marker = f"### COVER LETTER FOR JOB {i+2} ###" if i < len(job_contents_list)-1 else None
                
                start = full_response.find(current_marker)
                if start == -1:
                    logger.warning(f"Marker not found for job {i+1}")
                    cover_letters.append(f"Error: Could not find cover letter for job {i+1}")
                    continue
                
                start += len(current_marker)
                end = full_response.find(next_marker) if next_marker else None
                
                letter = full_response[start:end].strip() if end else full_response[start:].strip()
                cover_letters.append(letter if letter else f"Error: Empty cover letter for job {i+1}")
            
            logger.info(f"Successfully generated {len(cover_letters)} cover letters")
            return cover_letters

        except Exception as e:
            logger.error(f"Unexpected error in generate_multiple_cover_letters: {str(e)}")
            return ["Error: Unexpected error in generation"] * len(job_contents_list)

    # Rest of the class remains the same as in the previous version