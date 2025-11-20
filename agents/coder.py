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
        if reference_html:
            ref_soup = BeautifulSoup(reference_html, 'html.parser')
            ref_table = ref_soup.find('table')
            if ref_table:
                table_classes = ref_table.get('class', [])
                for table in soup.find_all('table'):
                    table['class'] = table_classes

        # CMS Specifics
        if cms_type.lower() == "opencart":
            # 1. Wrap images in <div class="img-responsive">
            for img in soup.find_all('img'):
                # Check if already wrapped (to avoid double wrapping if run multiple times)
                if img.parent.name == 'div' and 'img-responsive' in img.parent.get('class', []):
                    continue
                    
                new_div = soup.new_tag("div", **{"class": "img-responsive"})
                img.wrap(new_div)
                # Also add class to img itself if needed, but usually wrapper is enough for OC
                img['class'] = img.get('class', []) + ['img-responsive']

            # 2. Wrap tables in <div class="table-responsive">
            for table in soup.find_all('table'):
                if table.parent.name == 'div' and 'table-responsive' in table.parent.get('class', []):
                    continue
                new_div = soup.new_tag("div", **{"class": "table-responsive"})
                table.wrap(new_div)
                # Add Bootstrap table classes common in OC
                table['class'] = table.get('class', []) + ['table', 'table-bordered', 'table-hover']

            # 3. STRIP <script> and <iframe>
            for tag in soup(["script", "iframe"]):
                tag.decompose()
        
        return str(soup)

    def inject_internal_links(self, html_content, brand_name):
        """
        Scans text for opportunities to link to existing pages using Vector DB.
        Strategy: Exact match of Page Titles from Knowledge Base.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Get all known pages
        try:
            all_pages = self.vector_db.get_all_pages(brand_name)
        except Exception as e:
            # print(f"VectorDB Error: {e}")
            return html_content

        if not all_pages:
            return html_content

        # Sort by length (descending) to match longest phrases first
        # Filter out very short titles to avoid accidental matching of common words
        link_candidates = sorted(
            [p for p in all_pages if len(p.get('title', '')) > 4], 
            key=lambda x: len(x['title']), 
            reverse=True
        )
        
        # Track added links to avoid duplicates per page
        added_urls = set()

        # 2. Iterate over text nodes
        for text_node in soup.find_all(string=True):
            if text_node.parent.name in ['a', 'h1', 'h2', 'h3', 'script', 'style', 'code', 'pre']:
                continue
            
            text = text_node.string
            if not text:
                continue
                
            # Check for matches
            # Note: Modifying the tree while iterating is tricky. 
            # We will do a simple replacement if we find a match and stop for this node 
            # (to avoid nesting links or complex overlaps for MVP).
            
            for page in link_candidates:
                title = page['title']
                url = page['url']
                
                if url in added_urls:
                    continue
                    
                # Case-insensitive search
                start_index = text.lower().find(title.lower())
                if start_index != -1:
                    # Found a match!
                    original_text = text[start_index : start_index + len(title)]
                    
                    # Create new link tag
                    new_tag = soup.new_tag("a", href=url)
                    new_tag.string = original_text
                    new_tag['title'] = title
                    
                    # Split text node
                    before_text = text[:start_index]
                    after_text = text[start_index + len(title):]
                    
                    # Replace text_node with: before_text + link + after_text
                    # We need to insert these into the parent
                    parent = text_node.parent
                    
                    if before_text:
                        parent.insert(parent.index(text_node), before_text)
                    
                    parent.insert(parent.index(text_node), new_tag)
                    
                    if after_text:
                        # We need to insert after the link. 
                        # But wait, if we insert after, we might want to process it again?
                        # For MVP, let's just insert it and move on.
                        parent.insert(parent.index(text_node), after_text)
                    
                    # Remove original node
                    text_node.extract()
                    
                    added_urls.add(url)
                    break # Move to next text node (or stop processing this one since it's gone)
        
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
