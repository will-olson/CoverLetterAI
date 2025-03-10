# links.py
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobLinks:
    def __init__(self):
        self.job_links = [
            "https://climatebase.org/job/56506468/product-manager---pricing--marketplace?utm_source=jobs_directory&queryID=571e9b326cc2c020a03fa79eabb10c9e",
            "https://job-boards.greenhouse.io/chainguard/jobs/4423024006",
            "https://jobs.ashbyhq.com/DeepL/47ef3c02-2f1c-4281-8e89-f770f5377fd2/application",
            "https://job-boards.greenhouse.io/render/jobs/4417630005",
            "https://www.linkedin.com/jobs/view/4157798987",
            "https://www.linkedin.com/jobs/view/4157839999",
            "https://www.linkedin.com/jobs/view/4146187249",
            "https://www.linkedin.com/jobs/view/4154771717",
            "https://www.linkedin.com/jobs/view/4168245983",
            "https://www.linkedin.com/jobs/view/4149936812",
            "https://www.linkedin.com/jobs/view/4149942120",
            "https://www.linkedin.com/jobs/view/4150155115",
            "https://www.linkedin.com/jobs/view/3974165627",
            "https://www.linkedin.com/jobs/view/4149940238",
            "https://www.linkedin.com/jobs/view/4131585439",
            "https://www.linkedin.com/jobs/view/4143061357",
            "https://www.linkedin.com/jobs/view/4159672128",
            "https://www.linkedin.com/jobs/view/4159614468",
            "https://www.linkedin.com/jobs/view/4159611741",
            "https://www.linkedin.com/jobs/view/4133518359",
            "https://www.linkedin.com/jobs/view/4137362808",
            "https://www.linkedin.com/jobs/view/4175736235"
        ]
        self.cleaned_links = []
        self.clean_all_links()

    def clean_url(self, url: str) -> str:
        """Remove tracking parameters and clean URLs"""
        # Remove query parameters
        base_url = url.split('?')[0]
        # Remove trailing slash
        return base_url.rstrip('/')

    def clean_all_links(self):
        """Clean all job links"""
        self.cleaned_links = [self.clean_url(url) for url in self.job_links]
        logger.info(f"Cleaned {len(self.cleaned_links)} links")

    def get_source_type(self, url: str) -> str:
        """Determine the source of the job posting"""
        if 'linkedin.com' in url:
            return 'LinkedIn'
        elif 'greenhouse.io' in url:
            return 'Greenhouse'
        elif 'climatebase.org' in url:
            return 'ClimateBase'
        elif 'ashbyhq.com' in url:
            return 'Ashby'
        return 'Other'

    def group_links_by_source(self) -> Dict[str, List[str]]:
        """Group links by their source"""
        grouped = {}
        for link in self.cleaned_links:
            source = self.get_source_type(link)
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(link)
        return grouped

    def get_link_batches(self, batch_size: int = 3) -> List[List[str]]:
        """Return links in batches"""
        return [self.cleaned_links[i:i + batch_size] for i in range(0, len(self.cleaned_links), batch_size)]

    def save_to_json(self, filename: str = 'job_links.json'):
        """Save links and metadata to JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_links': len(self.cleaned_links),
            'sources': self.group_links_by_source(),
            'links': self.cleaned_links
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved links to {filename}")

    def load_from_json(self, filename: str = 'job_links.json') -> bool:
        """Load links from JSON"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.cleaned_links = data['links']
                logger.info(f"Loaded {len(self.cleaned_links)} links from {filename}")
                return True
        except Exception as e:
            logger.error(f"Error loading links: {str(e)}")
            return False

    def print_summary(self):
        """Print summary of job links"""
        grouped = self.group_links_by_source()
        print("\nJob Links Summary:")
        print("=" * 50)
        print(f"Total Links: {len(self.cleaned_links)}")
        print("\nBreakdown by Source:")
        for source, links in grouped.items():
            print(f"{source}: {len(links)} links")
        print("=" * 50)

# Usage example
if __name__ == "__main__":
    # Initialize job links
    job_links = JobLinks()
    
    # Print summary
    job_links.print_summary()
    
    # Save to JSON
    job_links.save_to_json()
    
    # Example of getting batches
    batches = job_links.get_link_batches(batch_size=3)
    print(f"\nNumber of batches (size 3): {len(batches)}")
    
    # Example of first batch
    print("\nFirst batch of links:")
    for link in batches[0]:
        print(f"- {link}")