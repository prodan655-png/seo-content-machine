import markdown
from bs4 import BeautifulSoup
from thefuzz import process
import os
import json

class Coder:
    def __init__(self, vector_db):
        self.vector_db = vector_db

    def convert_to_html(self, markdown_content, cms_type="OpenCart", reference_html=""):
        """
        Converts Markdown to HTML, applying CMS-specific formatting and reference patterns.
        """
        html = markdown.markdown(markdown_content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Apply Reference Patterns (Basic implementation: mimic table classes)
        ref_soup = BeautifulSoup(reference_html, 'html.parser')
        ref_table = ref_soup.find('table')
        if ref_table:
            table_classes = ref_table.get('class', [])
            for table in soup.find_all('table'):
                table['class'] = table_classes

        # CMS Specifics
        if cms_type == "OpenCart":
            # Wrap in container if needed, or specific classes
            # Example: Ensure images are responsive
            for img in soup.find_all('img'):
                img['class'] = img.get('class', []) + ['img-responsive']
        
        return str(soup)

    def inject_internal_links(self, html_content, brand_name):
        """
        Scans text for opportunities to link to existing pages using Vector DB.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        # This is a simplified approach. A full approach would iterate over text nodes.
        # For MVP, let's try to link the first occurrence of highly relevant terms.
        
        # Get all text nodes
        for text_node in soup.find_all(string=True):
            if text_node.parent.name in ['a', 'h1', 'h2', 'h3', 'script', 'style']:
                continue
            
            text = text_node.string
            if not text or len(text) < 10:
                continue

            # Query Vector DB for this text chunk to see if there's a relevant page
            # In reality, we'd extract keywords first. 
            # For MVP, let's just skip complex NLP here and rely on manual linking or 
            # simple keyword matching if we had a keyword list.
            # Since we have VectorDB, let's query it with the whole sentence? No, too broad.
            # Let's query with the first 5 words.
            query = " ".join(text.split()[:5])
            results = self.vector_db.query_similar(brand_name, query, n_results=1)
            
            if results:
                target = results[0]
                # Check if target title is in text (exact match)
                if target['title'] and target['title'].lower() in text.lower():
                    # Replace logic would go here. 
                    # Complex to do safely on raw string without breaking HTML.
                    # Skipping auto-replacement for MVP to avoid breaking text.
                    pass
        
        return str(soup)

    def inject_assets(self, html_content, asset_names):
        """
        Replaces image placeholders or fuzzy matches keywords to assets.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Replace explicit placeholders if any (e.g. <img src="placeholder">)
        # 2. Fuzzy match existing images
        # Strategy: Look for images with empty src or specific alt, OR
        # just look for keywords in text to insert images?
        # MVP: Let's assume the Writer puts <img alt="yeast"> and we match "yeast" to "angel_yeast.jpg"
        
        for img in soup.find_all('img'):
            query = img.get('alt', '')
            if not query:
                continue
                
            # Fuzzy match
            best_match = process.extractOne(query, asset_names)
            if best_match and best_match[1] > 60: # Threshold
                filename = best_match[0]
                img['src'] = f"/image/catalog/assets/{filename}" # OpenCart path convention
            else:
                img['src'] = "placeholder.jpg" # Fallback
                
        return str(soup)

    def generate_metadata(self, title, content):
        """
        Generates Meta Title, Description.
        """
        # Simple truncation for MVP
        description = content[:150] + "..."
        return {
            "meta_title": title,
            "meta_description": description,
            "og_title": title
        }

    def generate_schema(self, faq_list):
        """
        Generates JSON-LD for FAQPage.
        """
        if not faq_list:
            return ""
            
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        }
        
        for q in faq_list:
            schema["mainEntity"].append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Answer to be generated..." # Writer should provide answers too ideally
                }
            })
            
        return json.dumps(schema, indent=2)

    def validate_html(self, html_content, cms_type):
        """
        Validates and cleans HTML.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Strip scripts
        for script in soup(["script", "style"]):
            script.decompose()
            
        # CMS specific checks
        if cms_type == "OpenCart":
            # Ensure no div wrappers that break layout?
            pass
            
        return str(soup)
