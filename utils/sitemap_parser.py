import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse

def ingest_sitemap(url, max_pages=10000):
    """
    Parses a sitemap XML (handles nested sitemaps) and extracts URL, Title, and H1.
    Uses ThreadPoolExecutor for concurrent crawling.
    Returns a DataFrame.
    """
    import concurrent.futures
    import time
    
    all_urls = []
    
    def fetch_urls(sitemap_url):
        try:
            response = requests.get(sitemap_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'xml')
            
            # Check for nested sitemaps
            sitemaps = soup.find_all('sitemap')
            if sitemaps:
                # print(f"Found nested sitemap index: {sitemap_url}")
                for sm in sitemaps:
                    loc = sm.find('loc')
                    if loc:
                        fetch_urls(loc.text)
            else:
                # Standard urlset
                locs = soup.find_all('loc')
                # print(f"Found {len(locs)} URLs in {sitemap_url}")
                for loc in locs:
                    all_urls.append(loc.text)
                    
        except Exception as e:
            # print(f"Error fetching sitemap {sitemap_url}: {e}")
            pass

    # 1. Collect all URLs
    # print(f"Fetching sitemap structure from: {url}")
    fetch_urls(url)
    
    # Remove duplicates
    unique_urls = list(set(all_urls))
    # print(f"Total unique URLs found: {len(unique_urls)}")
    
    # Limit if specified (default is high)
    target_urls = unique_urls[:max_pages]
    
    data = []
    processed_count = 0
    total_count = len(target_urls)
    
    # Session for connection pooling - NOT thread safe to share!
    # We will create a session per request or just use requests.get (which is fine for this volume)
    # Or better: create a session inside the thread.
    
    def process_url(page_url):
        nonlocal processed_count
        try:
            # Create a new session for thread safety (or just use requests.get)
            with requests.Session() as session:
                session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
                
                page_res = session.get(page_url, timeout=10)
                
                if page_res.status_code == 200:
                    page_soup = BeautifulSoup(page_res.content, 'html.parser')
                    title = page_soup.title.string.strip() if page_soup.title and page_soup.title.string else ""
                    
                    h1_tag = page_soup.find('h1')
                    h1 = h1_tag.get_text(strip=True) if h1_tag else ""
                    
                    if not h1:
                        h1 = title
                    
                    # Print progress every 10 pages to avoid spamming terminal
                    # if processed_count % 10 == 0:
                    #    print(f"Processed {processed_count}/{total_count}")
                    
                    return {
                        "url": page_url,
                        "title": title,
                        "h1": h1
                    }
        except Exception as e:
            # print(f"Failed to parse {page_url}: {e}")
            pass
        finally:
            processed_count += 1
            
        return None

    # 2. Concurrent Crawling
    # Reduce workers to 5 to be safer and avoid overwhelming the server/local network
    # print(f"Starting concurrent crawl of {total_count} pages with 5 workers...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_url, target_urls))
        
    # Filter None results
    data = [r for r in results if r]
            
    return pd.DataFrame(data)
