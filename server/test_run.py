# test_run.py
from dotenv import load_dotenv
import os
import logging
from app import CoverLetterGenerator
import pandas as pd
from links import JobLinks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_file(batch_size=None):
    """Create test file with job links"""
    # Initialize JobLinks
    job_links = JobLinks()
    
    # Print summary of all links
    job_links.print_summary()
    
    # Get all links or a batch if specified
    if batch_size:
        batches = job_links.get_link_batches(batch_size)
        links_to_process = batches[0]  # Just take the first batch for testing
        logger.info(f"Using first batch of {len(links_to_process)} links")
    else:
        links_to_process = job_links.cleaned_links
        logger.info(f"Using all {len(links_to_process)} links")

    # Create DataFrame and save to Excel
    test_data = {
        'job_link': links_to_process
    }
    df = pd.DataFrame(test_data)
    df.to_excel('test_jobs.xlsx', index=False)
    logger.info(f"Created test_jobs.xlsx with {len(links_to_process)} jobs")
    
    # Save links to JSON for reference
    job_links.save_to_json('processed_jobs.json')

def run_test(batch_size=3):
    try:
        # Create test file with specified batch size
        create_test_file(batch_size)
        
        # Load environment variables
        load_dotenv()
        
        # Verify OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.error("OPENAI_API_KEY not found in .env file")
            return
        
        # Read resume
        logger.info("Reading resume file...")
        try:
            with open('resume.txt', 'r') as file:
                resume_text = file.read()
        except FileNotFoundError:
            logger.error("resume.txt not found in current directory")
            return
        
        # Initialize generator
        logger.info("Initializing CoverLetterGenerator...")
        generator = CoverLetterGenerator(
            resume_text=resume_text,
            openai_api_key=openai_api_key
        )
        
        # Process jobs
        logger.info(f"Processing jobs in batches of {batch_size}...")
        generator.process_job_links(
            excel_path='test_jobs.xlsx',
            output_path='test_output_cover_letters.xlsx',
            batch_size=batch_size
        )
        
        logger.info("Processing complete! Check test_output_cover_letters.xlsx")
        
        # Validate output
        if os.path.exists('test_output_cover_letters.xlsx'):
            df = pd.read_excel('test_output_cover_letters.xlsx')
            logger.info(f"Generated {len(df)} cover letters")
            
            # Check for any errors in cover letters
            errors = df[df['cover_letter'].str.contains('Error', na=False)]
            if not errors.empty:
                logger.warning(f"Found {len(errors)} errors in cover letter generation")
        else:
            logger.warning("Output file not created")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if 'generator' in locals():
            del generator

def run_small_test():
    """Run a test with just a few links first"""
    logger.info("Running small test with 3 links...")
    run_test(batch_size=3)

def run_full_test():
    """Run test with all links"""
    logger.info("Running full test with all links...")
    run_test(batch_size=10)

if __name__ == "__main__":
    # Uncomment the test you want to run
    run_small_test()  # Test with just 3 links
    # run_full_test()  # Test with all links