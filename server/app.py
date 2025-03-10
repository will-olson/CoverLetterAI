import pandas as pd
import re
import json
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

    def extract_professional_context(self):
        """
        Extract comprehensive professional context from resume
        """
        try:
            # Extract key professional highlights
            professional_summary = self.extract_professional_summary()
            key_achievements = self.extract_key_achievements()
            skill_matrix = self.create_skill_matrix()

            return {
                "professional_summary": professional_summary,
                "key_achievements": key_achievements,
                "skill_matrix": skill_matrix
            }
        except Exception as e:
            logger.error(f"Error extracting professional context: {str(e)}")
            return {}

    def extract_professional_summary(self):
        """Extract a concise professional summary"""
        # Use regex or NLP to identify key career moments
        summary_match = re.search(r'(Professional Summary|Career Objective):(.*?)(?:\n\n|\Z)', 
                                   self.resume, re.DOTALL | re.IGNORECASE)
        return summary_match.group(2).strip() if summary_match else self.resume[:500]

    def extract_key_achievements(self):
        """Extract top 3-5 career achievements"""
        # Look for achievement-oriented language
        achievement_patterns = [
            r'Achieved', r'Increased', r'Improved', r'Led', r'Developed',
            r'Launched', r'Reduced', r'Optimized', r'Transformed'
        ]
        
        achievements = []
        for pattern in achievement_patterns:
            matches = re.findall(f'{pattern}.*?(?:\n|$)', self.resume, re.IGNORECASE)
            achievements.extend(matches[:3])
        
        return achievements[:5]

    def create_skill_matrix(self):
        """Create a structured skill matrix"""
        # Extract skills using various patterns
        skill_sections = [
            r'Skills:(.*?)(?:\n\n|\Z)',
            r'Technical Skills:(.*?)(?:\n\n|\Z)',
            r'Professional Skills:(.*?)(?:\n\n|\Z)'
        ]
        
        skills = {}
        for section_pattern in skill_sections:
            match = re.search(section_pattern, self.resume, re.DOTALL | re.IGNORECASE)
            if match:
                section_skills = re.findall(r'\b\w+\b', match.group(1))
                skills.update({skill.lower(): True for skill in section_skills})
        
        return list(skills.keys())

    def extract_page_content(self, html_content):
        """Enhanced precise job description content extraction"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for unwanted in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            unwanted.decompose()

        # Advanced selector strategy
        selectors = [
            '.jobs-description-content__text',
            '.description__text',
            '.greenhouse-job-description',
            '.job-description',
            '#job-description',
            '[data-testid="job-description"]',
            'main', 
            'article', 
            'div[class*="content"]', 
            'div[class*="description"]'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                # Combine and score paragraphs
                paragraphs = []
                for element in elements:
                    paras = element.find_all(['p', 'li'])
                    scored_paras = [
                        (p.get_text(strip=True), len(p.get_text(strip=True).split())) 
                        for p in paras
                    ]
                    # Sort by paragraph length, take top paragraphs
                    paragraphs.extend(
                        [p[0] for p in sorted(scored_paras, key=lambda x: x[1], reverse=True)[:5]]
                    )
                
                # Combine and clean
                content = ' '.join(paragraphs)
                return ' '.join(content.split())[:2500]
        
        # Ultimate fallback
        return ' '.join(soup.get_text(strip=True).split())[:2000]

    def generate_multiple_cover_letters(self, job_contents_list):
        """Strategic, context-rich cover letter generation"""
        try:
            # Extract comprehensive professional context
            professional_context = self.extract_professional_context()
            
            # Construct strategic prompt
            prompt = (
                "You are an elite career strategist crafting transformative career narratives. "
                "Your goal is to create highly personalized, impactful cover letters. "
                
                f"COMPREHENSIVE PROFESSIONAL PROFILE: {json.dumps(professional_context, indent=2)} "
                
                "CRITICAL EVALUATION CRITERIA: "
                "1. Demonstrate profound understanding of professional journey. "
                "2. Highlight most relevant experiences for each specific role. "
                "3. Create a narrative that proves candidacy. "
                "4. Maintain a tone reflecting unique professional brand. "
                "5. Include specific, quantifiable achievements. "
                
                f"JOB POSTINGS TO ANALYZE: {' '.join([f'JOB {i+1} DETAILS: {content}' for i, content in enumerate(job_contents_list)])} "
                
                "COVER LETTER GUIDELINES: "
                "- Open with a compelling, role-specific hook "
                "- Demonstrate deep understanding of company and role "
                "- Connect 2-3 specific career achievements directly to requirements "
                "- Close with a forward-looking, confident statement "
                
                "FORMAT INSTRUCTIONS: "
                "Provide cover letters marked as: ### COVER LETTER FOR JOB {number} ### "
                "Ensure each letter is highly tailored and achievement-driven."
            )

            # API request configuration
            api_data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are an elite career strategist who crafts transformative career narratives."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }

            # Send API request
            logger.info("Sending strategic cover letter generation request")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}"
                },
                json=api_data,
                timeout=45
            )
            
            response.raise_for_status()
            
            # Parse and extract cover letters
            full_response = response.json()['choices'][0]['message']['content'].strip()
            
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
            
            logger.info(f"Successfully generated {len(cover_letters)} strategic cover letters")
            return cover_letters

        except Exception as e:
            logger.error(f"Unexpected error in strategic cover letter generation: {str(e)}")
            return ["Error: Unexpected error in generation"] * len(job_contents_list)
        
    def scrape_job_content(self, url):
        """Scrape job content from a given URL"""
        try:
            # Navigate to the URL
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

    def process_job_links(self, excel_path, output_path, batch_size=5):
        """Process job links in optimal batch sizes"""
        try:
            df = pd.read_excel(excel_path)
            results = []
            
            # Calculate optimal batch size based on total jobs
            total_jobs = len(df)
            if total_jobs > 5:
                logger.info("Large number of jobs detected, processing in smaller batches")
                batch_size = 5  # Maximum 5 jobs per batch to stay within context window
            
            # Process jobs in batches
            for i in range(0, total_jobs, batch_size):
                batch_df = df[i:i+batch_size]
                current_batch_size = len(batch_df)
                logger.info(f"Processing batch {i//batch_size + 1} of {(total_jobs + batch_size - 1)//batch_size}")
                logger.info(f"Batch size: {current_batch_size} jobs")
                
                # Scrape content for all jobs in batch
                job_contents = []
                job_urls = []
                for _, row in batch_df.iterrows():
                    url = row['job_link']
                    content = self.scrape_job_content(url)
                    job_contents.append(content)
                    job_urls.append(url)
                    time.sleep(2)  # Delay between scraping
                
                try:
                    # Generate cover letters for batch
                    cover_letters = self.generate_multiple_cover_letters(job_contents)
                    
                    # Store results
                    for url, content, letter in zip(job_urls, job_contents, cover_letters):
                        results.append({
                            'job_link': url,
                            'job_content': content,
                            'cover_letter': letter
                        })
                    
                    # Optional delay between batches if processing multiple batches
                    if i + batch_size < len(df):
                        time.sleep(5)
                
                except Exception as e:
                    logger.error(f"Error processing batch: {str(e)}")
                    # Add error entries for this batch
                    for url, content in zip(job_urls, job_contents):
                        results.append({
                            'job_link': url,
                            'job_content': content,
                            'cover_letter': "Error generating cover letter"
                        })
            
            # Save results
            results_df = pd.DataFrame(results)
            results_df.to_excel(output_path, index=False)
            logger.info(f"Results saved to {output_path}")
            
            # Log summary
            success_count = len([r for r in results if not r['cover_letter'].startswith("Error")])
            logger.info(f"Successfully generated {success_count} out of {len(df)} cover letters")
            
        except Exception as e:
            logger.error(f"Error in process_job_links: {str(e)}")
            raise

    def __del__(self):
        """Clean up browser instance"""
        try:
            self.driver.quit()
        except:
            pass