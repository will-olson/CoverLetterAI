# test_linkedin.py
from dotenv import load_dotenv
import os
import logging
import argparse
import pandas as pd
from app import CoverLetterGenerator
from links import JobLinks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInCoverLetterTester:
    def __init__(self):
        # Load job links
        self.job_links = JobLinks()
        
        # Filter only LinkedIn links
        self.linkedin_links = [
            link for link in self.job_links.cleaned_links 
            if 'linkedin.com/jobs/view/' in link
        ]

    def create_test_file(self, num_links=5):
        """
        Create a test file with specified number of LinkedIn links
        
        Args:
            num_links (int): Number of links to process. 
                             Use -1 for all LinkedIn links
        """
        # Determine links to use
        if num_links == -1:
            links_to_process = self.linkedin_links
        else:
            links_to_process = self.linkedin_links[:num_links]
        
        logger.info(f"Total LinkedIn links available: {len(self.linkedin_links)}")
        logger.info(f"Processing {len(links_to_process)} LinkedIn links")

        # Create DataFrame
        test_data = {
            'job_link': links_to_process
        }
        df = pd.DataFrame(test_data)
        df.to_excel('linkedin_test_jobs.xlsx', index=False)
        
        return len(links_to_process)

    def run_linkedin_test(self, num_links=5, batch_size=None):
        """
        Run cover letter generation test for LinkedIn links
        
        Args:
            num_links (int): Number of links to process
            batch_size (int, optional): Batch size for processing. 
                                        If None, use num_links
        """
        try:
            # Load environment variables
            load_dotenv()
            
            # Verify OpenAI API key
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                logger.error("OPENAI_API_KEY not found in .env file")
                return
            
            # Read resume
            try:
                with open('resume.txt', 'r') as file:
                    resume_text = file.read()
            except FileNotFoundError:
                logger.error("resume.txt not found in current directory")
                return
            
            # Create test file
            total_jobs = self.create_test_file(num_links)
            
            # Determine batch size
            if batch_size is None:
                batch_size = total_jobs
            
            # Initialize generator
            generator = CoverLetterGenerator(
                resume_text=resume_text,
                openai_api_key=openai_api_key
            )
            
            # Process jobs
            output_file = f'linkedin_output_{num_links}_links.xlsx'
            generator.process_job_links(
                excel_path='linkedin_test_jobs.xlsx',
                output_path=output_file,
                batch_size=batch_size
            )
            
            # Analyze results
            self.analyze_results(output_file)
            
        except Exception as e:
            logger.error(f"Error during LinkedIn test: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def analyze_results(self, output_file):
        """
        Analyze cover letter generation results
        
        Args:
            output_file (str): Path to the output Excel file
        """
        try:
            df = pd.read_excel(output_file)
            
            # Basic statistics
            total_jobs = len(df)
            successful_jobs = df[~df['cover_letter'].str.contains('Error', na=False)]
            
            logger.info("\n--- LinkedIn Cover Letter Generation Results ---")
            logger.info(f"Total Jobs Processed: {total_jobs}")
            logger.info(f"Successful Cover Letters: {len(successful_jobs)}")
            logger.info(f"Success Rate: {len(successful_jobs) / total_jobs * 100:.2f}%")
            
            # Detailed error analysis
            if len(successful_jobs) < total_jobs:
                errors = df[df['cover_letter'].str.contains('Error', na=False)]
                logger.warning("\nError Details:")
                for idx, row in errors.iterrows():
                    logger.warning(f"Error in job: {row['job_link']}")
            
        except Exception as e:
            logger.error(f"Error analyzing results: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='LinkedIn Cover Letter Generation Test')
    parser.add_argument('-n', '--num_links', type=int, default=5, 
                        help='Number of LinkedIn links to process. Use -1 for all links.')
    parser.add_argument('-b', '--batch_size', type=int, default=None, 
                        help='Batch size for processing. Defaults to num_links if not specified.')
    
    args = parser.parse_args()
    
    tester = LinkedInCoverLetterTester()
    tester.run_linkedin_test(num_links=args.num_links, batch_size=args.batch_size)

if __name__ == "__main__":
    main()