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
        """Extract all relevant text content from the page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for unwanted in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            unwanted.decompose()

        # Get all text content
        text_content = ' '.join(p.text.strip() for p in soup.find_all(['p', 'div', 'span', 'li']) if p.text.strip())
        
        # Clean up the text
        text_content = ' '.join(text_content.split())  # Remove extra whitespace
        return text_content

    def scrape_job_content(self, url):
        """Scrape all text content from the job posting"""
        try:
            self.driver.get(url)
            time.sleep(3)  # Allow page to load
            
            # Get the page source after JavaScript rendering
            page_source = self.driver.page_source
            
            # Extract text content
            text_content = self.extract_page_content(page_source)
            
            if not text_content:
                # Fallback: get all visible text
                text_content = self.driver.find_element(By.TAG_NAME, 'body').text
            
            logger.info(f"Successfully scraped content from: {url}")
            return text_content.strip()

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return "Error scraping job content"

    def generate_multiple_cover_letters(self, job_contents_list):
        """Generate multiple cover letters in a single API request with token management"""
        try:
            logger.info(f"Preparing to generate {len(job_contents_list)} cover letters")
            
            # Calculate approximate tokens (rough estimate: 1 token ≈ 4 characters)
            TOKENS_PER_CHAR = 0.25
            MAX_TOKENS = 7000  # Leave some buffer for the response
            
            # Calculate token estimates
            resume_tokens = len(str(self.resume)) * TOKENS_PER_CHAR
            instruction_tokens = 500  # Approximate tokens for system message and instructions
            available_tokens = MAX_TOKENS - resume_tokens - instruction_tokens
            
            # Calculate tokens per job description
            tokens_per_job = available_tokens / len(job_contents_list)
            max_chars_per_job = int(tokens_per_job / TOKENS_PER_CHAR)
            
            logger.info(f"Estimated tokens per job: {tokens_per_job}")
            
            # Format job contents with proper numbering and length limits
            formatted_jobs = []
            for i, content in enumerate(job_contents_list, 1):
                # Truncate content to fit token budget
                content_str = str(content)[:max_chars_per_job]
                formatted_jobs.append(f"### JOB POSTING {i} ###\n{content_str}")

            # Combine all job postings
            combined_jobs = "\n\n".join(formatted_jobs)
            
            # Prepare resume (truncated if needed)
            resume_max_chars = int(2000 * TOKENS_PER_CHAR)  # Allow ~500 tokens for resume
            resume_text = str(self.resume)[:resume_max_chars]
            
            # Construct prompt
            prompt = f"""
            Based on the following resume and {len(job_contents_list)} job postings, write distinct professional cover letters for each position.

            Resume:
            {resume_text}

            Job Postings:
            {combined_jobs}

            For each job posting, provide a separate cover letter following this format:

            ### COVER LETTER FOR JOB 1 ###
            [Cover letter content here]

            Each cover letter should:
            1. Extract relevant job details from the content (title, company, requirements)
            2. Highlight matching experience from the resume
            3. Use specific examples to demonstrate qualifications
            4. Show enthusiasm for the role and company
            5. Maintain a professional tone
            6. Be concise (max 400 words per letter)

            Provide {len(job_contents_list)} separate cover letters, clearly marked with the job number.
            """

            # Prepare API request
            api_data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a professional cover letter writer."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
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
            if response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}")
                return ["Error: API request failed"] * len(job_contents_list)
            
            # Parse response
            try:
                response_data = response.json()
                full_response = response_data['choices'][0]['message']['content'].strip()
            except (KeyError, IndexError) as e:
                logger.error(f"Error parsing API response: {str(e)}")
                return ["Error: Failed to parse API response"] * len(job_contents_list)
            
            # Extract individual cover letters
            cover_letters = []
            for i in range(len(job_contents_list)):
                try:
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
                    if letter:
                        cover_letters.append(letter)
                    else:
                        cover_letters.append(f"Error: Empty cover letter for job {i+1}")
                
                except Exception as e:
                    logger.error(f"Error extracting cover letter {i+1}: {str(e)}")
                    cover_letters.append(f"Error: Failed to extract cover letter {i+1}")
            
            # Ensure we have the right number of cover letters
            while len(cover_letters) < len(job_contents_list):
                cover_letters.append("Error: Missing cover letter")
            
            logger.info(f"Successfully generated {len(cover_letters)} cover letters")
            return cover_letters

        except Exception as e:
            logger.error(f"Unexpected error in generate_multiple_cover_letters: {str(e)}")
            return ["Error: Unexpected error in generation"] * len(job_contents_list)

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