import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse

def ingest_sitemap(url):
    """
    Parses a sitemap XML and extracts URL, Title, and H1 for each page.
    Returns a DataFrame.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        
        data = []
        
        # Limit to first 50 for MVP speed, or remove limit for full production
        # For MVP, let's be polite and robust
        for page_url in urls[:20]: # MVP Limit
            try:
                page_res = requests.get(page_url, timeout=10)
                if page_res.status_code == 200:
                    page_soup = BeautifulSoup(page_res.content, 'html.parser')
                    title = page_soup.title.string if page_soup.title else ""
                    h1 = page_soup.find('h1').get_text(strip=True) if page_soup.find('h1') else ""
                    
                    data.append({
                        "url": page_url,
                        "title": title,
                        "h1": h1
                    })
            except Exception as e:
                print(f"Failed to parse {page_url}: {e}")
                continue
                
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return pd.DataFrame(columns=["url", "title", "h1"])
