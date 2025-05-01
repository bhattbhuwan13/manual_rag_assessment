import os
from firecrawl import FirecrawlApp, ScrapeOptions
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Firecrawl client
client = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))

def save_content(content, filename):
    """Save content to a file in the data directory"""
    os.makedirs('data', exist_ok=True)
    filepath = os.path.join('data', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    print(f"Saved content to {filepath}")

def main():
    # URL to crawl
    url = "https://joinvoy.zendesk.com/hc/en-gb"
    
    try:
        # Start the crawl
        print(f"Starting crawl of {url}")
        crawl_result = client.crawl_url(
            url=url,
            limit= 30,  # We can increase this if we want   
            scrape_options=ScrapeOptions(formats=['markdown'])
        )
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"voy_zendesk_content_{timestamp}.md"
        
        # Save the content
        save_content(crawl_result, filename)
        print("Crawl completed successfully!")
        
    except Exception as e:
        print(f"Error during crawling: {str(e)}")

if __name__ == "__main__":
    main() 