# test_run.py
from dotenv import load_dotenv
import os
import logging
from app import CoverLetterGenerator
import pandas as pd
from links import JobLinks
import time
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_test_file(start_index=0, batch_size=5, num_batches=3):
    """Create test file with specified batch of job links"""
    # Initialize JobLinks
    job_links = JobLinks()
    
    # Print summary of all links
    job_links.print_summary()
    
    # Calculate indices for the batch
    end_index = start_index + (batch_size * num_batches)
    links_to_process = job_links.cleaned_links[start_index:end_index]
    
    logger.info(f"Processing links {start_index + 1} to {end_index} (Total: {len(links_to_process)})")

    # Create DataFrame and save to Excel
    test_data = {
        'job_link': links_to_process
    }
    df = pd.DataFrame(test_data)
    df.to_excel('test_jobs.xlsx', index=False)
    logger.info(f"Created test_jobs.xlsx with {len(links_to_process)} jobs")
    
    # Save links to JSON for reference
    job_links.save_to_json('processed_jobs.json')
    return len(links_to_process)

def run_batch_test(start_index=0, batch_size=5, num_batches=3):
    """Run test for a specific range of jobs"""
    try:
        # Create test file with specified range
        num_jobs = create_test_file(start_index, batch_size, num_batches)
        
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
        logger.info(f"Processing {num_jobs} jobs in batches of {batch_size}...")
        
        # Create output filename with batch range
        output_file = f'test_output_batch_{start_index+1}_to_{start_index + num_jobs}.xlsx'
        
        generator.process_job_links(
            excel_path='test_jobs.xlsx',
            output_path=output_file,
            batch_size=batch_size
        )
        
        logger.info(f"Processing complete! Check {output_file}")
        
        # Validate output
        if os.path.exists(output_file):
            df = pd.read_excel(output_file)
            logger.info(f"Generated {len(df)} cover letters")
            
            # Check for any errors in cover letters
            errors = df[df['cover_letter'].str.contains('Error', na=False)]
            if not errors.empty:
                logger.warning(f"Found {len(errors)} errors in cover letter generation")
                for idx, row in errors.iterrows():
                    logger.warning(f"Error in job {idx + 1}: {row['job_link']}")
            else:
                logger.info("All cover letters generated successfully!")
        else:
            logger.warning("Output file not created")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        if 'generator' in locals():
            del generator

def process_all_links_in_batches(batch_size=5, delay_between_batches=300):  # 5 minute delay
    """Process all links in multiple batches with delays"""
    job_links = JobLinks()
    total_links = len(job_links.cleaned_links)
    num_batches = (total_links + batch_size - 1) // batch_size  # Round up division
    
    logger.info(f"Starting processing of {total_links} links in {num_batches} batches")
    
    for batch_num in range(num_batches):
        start_index = batch_num * batch_size
        logger.info(f"\nProcessing Batch {batch_num + 1} of {num_batches}")
        
        # Process current batch
        run_batch_test(
            start_index=start_index,
            batch_size=batch_size,
            num_batches=1
        )
        
        # Delay between batches (except for the last batch)
        if batch_num < num_batches - 1:
            logger.info(f"Waiting {delay_between_batches} seconds before next batch...")
            time.sleep(delay_between_batches)

if __name__ == "__main__":
    try:
        # Process all links in batches of 5 with delays
        process_all_links_in_batches(
            batch_size=5,
            delay_between_batches=300  # 5 minutes between batches
        )
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())