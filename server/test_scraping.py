# test_scraping.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import logging
import pandas as pd
from links import JobLinks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        # Set up Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-notifications')
        # chrome_options.add_argument('--headless')  # Uncomment for headless mode
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def extract_page_content(self, html_content, url):
        """
        Extract precise job description content with platform-specific strategies
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for unwanted in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            unwanted.decompose()

        # Platform-specific selectors
        platform_selectors = {
            'linkedin.com': [
                '.jobs-description-content__text',
                '.description__text',
                '.jobs-box__html-content',
                '[data-job-description-content]'
            ],
            'greenhouse.io': [
                '.greenhouse-job-description',
                '.job-description',
                '#job_description',
                '.field-group-format-wrapper'
            ],
            'climatebase.org': [
                '.job-details',
                '.job-description',
                '[data-testid="job-description"]'
            ],
            'ashbyhq.com': [
                '.job-description-section',
                '.job-description',
                '[data-testid="job-description"]'
            ]
        }

        # Determine platform
        platform = next((p for p in platform_selectors if p in url), 'generic')
        
        # Selectors to try
        selectors_to_try = platform_selectors.get(platform, []) + [
            '#job-description',
            '.job-description',
            '[data-testid="job-description"]',
            'main',
            'article',
            'div[class*="content"]',
            'div[class*="description"]'
        ]

        # Try specific selectors
        for selector in selectors_to_try:
            description_elements = soup.select(selector)
            
            if description_elements:
                # Combine text from all matching elements
                paragraphs = []
                for element in description_elements:
                    # Find meaningful paragraphs
                    paras = element.find_all(['p', 'li'])
                    paragraphs.extend([
                        p.get_text(strip=True) 
                        for p in paras 
                        if len(p.get_text(strip=True).split()) > 5
                    ])
                
                # Combine and clean text
                if paragraphs:
                    content = ' '.join(paragraphs)
                    logger.info(f"Content extracted using selector: {selector}")
                    return content[:2000]  # Limit length
        
        # Fallback: extract all text
        return ' '.join(soup.get_text(strip=True).split())[:1000]

    def scrape_job_content(self, url):
        """Enhanced job content scraping with platform-specific handling"""
        try:
            self.driver.get(url)
            time.sleep(3)  # Allow page to load
            
            # Platform-specific preprocessing
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
            text_content = self.extract_page_content(page_source, url)
            
            logger.info(f"Successfully scraped content from: {url}")
            return text_content.strip()

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return "Error scraping job content"

    def batch_scrape_jobs(self, urls, output_path='job_scraping_results.xlsx'):
        """Batch scrape multiple job links"""
        results = []
        
        for url in urls:
            try:
                content = self.scrape_job_content(url)
                results.append({
                    'job_link': url,
                    'job_content': content,
                    'content_length': len(content)
                })
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
        
        # Save results to Excel
        results_df = pd.DataFrame(results)
        results_df.to_excel(output_path, index=False)
        logger.info(f"Scraping results saved to {output_path}")
        
        # Print summary
        logger.info("\nScraping Summary:")
        logger.info(f"Total URLs processed: {len(results)}")
        logger.info(f"Average content length: {results_df['content_length'].mean():.2f}")
        logger.info(f"Min content length: {results_df['content_length'].min()}")
        logger.info(f"Max content length: {results_df['content_length'].max()}")

    def __del__(self):
        """Clean up browser instance"""
        try:
            self.driver.quit()
        except:
            pass

def run_scraping_test():
    """Run comprehensive scraping test"""
    # Initialize job links
    job_links = JobLinks()
    
    # Create scraper
    scraper = JobScraper()
    
    # Batch scrape jobs
    scraper.batch_scrape_jobs(job_links.cleaned_links)

if __name__ == "__main__":
    run_scraping_test()