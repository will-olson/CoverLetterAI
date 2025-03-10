# test_prompt_engineering.py
from dotenv import load_dotenv
import os
import logging
import pandas as pd
from app import CoverLetterGenerator
from links import JobLinks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PromptEngineeringComparator:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Read resume
        try:
            with open('resume.txt', 'r') as file:
                self.resume_text = file.read()
        except FileNotFoundError:
            logger.error("resume.txt not found in current directory")
            self.resume_text = ""
        
        # Get OpenAI API key
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.error("OPENAI_API_KEY not found in .env file")

    def run_prompt_comparison(self, links):
        """
        Compare different prompt engineering approaches
        
        Args:
            links (list): List of job links to test
        """
        # Prepare different generator instances with the same resume
        generators = {
            "Original Approach": CoverLetterGenerator(
                resume_text=self.resume_text, 
                openai_api_key=self.openai_api_key
            ),
        }
        
        # Results storage
        comparison_results = []
        
        # Process links with each generator
        for approach_name, generator in generators.items():
            try:
                # Scrape job contents
                job_contents = []
                for url in links:
                    content = generator.scrape_job_content(url)
                    job_contents.append(content)
                
                # Generate cover letters
                cover_letters = generator.generate_multiple_cover_letters(job_contents)
                
                # Store results
                for url, content, letter in zip(links, job_contents, cover_letters):
                    comparison_results.append({
                        'Approach': approach_name,
                        'Job Link': url,
                        'Job Content': content,
                        'Cover Letter': letter
                    })
            
            except Exception as e:
                logger.error(f"Error with {approach_name}: {str(e)}")
        
        # Create comparison DataFrame
        comparison_df = pd.DataFrame(comparison_results)
        
        # Save comparison results
        comparison_df.to_excel('prompt_engineering_comparison.xlsx', index=False)
        
        # Analyze and log results
        self.analyze_comparison_results(comparison_df)
        
        return comparison_df

    def analyze_comparison_results(self, comparison_df):
        """
        Analyze and log comparison results
        
        Args:
            comparison_df (pd.DataFrame): Comparison results DataFrame
        """
        if comparison_df.empty:
            logger.error("No results to analyze. DataFrame is empty.")
            return

        logger.info("\n--- Prompt Engineering Comparison ---")
        
        # Group by approach
        for approach in comparison_df['Approach'].unique():
            approach_df = comparison_df[comparison_df['Approach'] == approach]
            
            # Calculate metrics
            total_jobs = len(approach_df)
            error_jobs = approach_df[approach_df['Cover Letter'].str.contains('Error', na=False)]
            
            logger.info(f"\nApproach: {approach}")
            logger.info(f"Total Jobs: {total_jobs}")
            logger.info(f"Successful Cover Letters: {total_jobs - len(error_jobs)}")
            logger.info(f"Success Rate: {(total_jobs - len(error_jobs)) / total_jobs * 100:.2f}%")
            
            # Log error details if any
            if len(error_jobs) > 0:
                logger.warning("Error Details:")
                for idx, row in error_jobs.iterrows():
                    logger.warning(f"Error in job: {row['Job Link']}")

def main():
    # Initialize comparator
    comparator = PromptEngineeringComparator()
    
    # Get LinkedIn links from JobLinks
    job_links = JobLinks()
    linkedin_links = [
        link for link in job_links.cleaned_links 
        if 'linkedin.com/jobs/view/' in link
    ]
    
    # Select first two LinkedIn links
    test_links = linkedin_links[:2]
    
    # Run comparison
    comparison_results = comparator.run_prompt_comparison(test_links)

if __name__ == "__main__":
    main()