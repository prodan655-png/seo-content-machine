from utils.ai_handler import AIHandler
import json

from bs4 import BeautifulSoup

class Writer:
    def __init__(self, api_key):
        self.ai_handler = AIHandler(api_key, model_name="gemini-2.5-flash")

    def analyze_reference(self, html_content):
        """
        Analyzes a reference HTML file to extract structural patterns and CSS classes.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        patterns = {
            "h1_class": [],
            "h2_class": [],
            "h3_class": [],
            "p_class": [],
            "ul_class": [],
            "ol_class": [],
            "table_class": [],
            "img_class": []
        }

        # Extract classes for key elements
        for tag in ['h1', 'h2', 'h3', 'p', 'ul', 'ol', 'table', 'img']:
            elements = soup.find_all(tag)
            for el in elements:
                if el.get('class'):
                    patterns[f"{tag}_class"].extend(el.get('class'))
        
        # Deduplicate and format
        for key in patterns:
            patterns[key] = list(set(patterns[key]))
            
        return patterns

    def generate_outline(self, research_data, tov):
        """
        Generates a structured outline based on research and ToV.
        """
        competitor_summary = "\n".join([f"- {c['h1']}: {', '.join(c['structure'][:3])}..." for c in research_data.get('competitor_outlines', [])])
        
        prompt = f"""
        You are an expert SEO Content Writer. Create a detailed outline for an article about '{research_data['topic']}'.
        
        Context:
        - Intent: {research_data.get('intent')}
        - Competitors cover: 
        {competitor_summary}
        
        Tone of Voice:
        {tov}
        
        Requirements:
        - High CTR Title
        - Logical H2/H3 structure
        - Include an FAQ section
        - Focus on user value
        
        Return the outline in JSON format:
        {{
            "title": "Article Title",
            "sections": [
                {{"heading": "H2 Heading", "subheadings": ["H3 Subheading 1", "H3 Subheading 2"], "notes": "Key points to cover"}}
            ],
            "faq": ["Question 1", "Question 2"]
        }}
        """
        response = self.ai_handler.generate_content(prompt)
        try:
            return json.loads(response.text.replace('```json', '').replace('```', ''))
        except Exception as e:
            # print(f"Error parsing outline JSON: {e}")
            # Fallback outline
            return {
                "title": f"Guide to {research_data['topic']}",
                "sections": [{"heading": "Introduction", "subheadings": [], "notes": "Intro"}],
                "faq": []
            }

    def write_article(self, outline, tov, keywords, reference_patterns=None, internal_links=None):
        """
        Generates the full article content based on the approved outline and optional reference patterns.
        """
        outline_str = json.dumps(outline, indent=2)
        keywords_str = ", ".join(keywords)
        
        links_instruction = ""
        if internal_links:
            links_instruction = f"""
            INTERNAL LINKING (CRITICAL):
            You have access to the following existing pages on the site:
            {internal_links}
            
            Rules for Internal Linking:
            1. You MUST include at least 3-5 internal links to these pages where contextually relevant.
            2. Use natural anchor text (do not use "click here").
            3. Format: [Anchor Text](url)
            """
        
        style_instructions = ""
        if reference_patterns:
            style_instructions = f"""
            CRITICAL - USE THESE EXACT CSS CLASSES FROM REFERENCE:
            - H2 classes: {', '.join(reference_patterns.get('h2_class', []))}
            - H3 classes: {', '.join(reference_patterns.get('h3_class', []))}
            - Paragraph classes: {', '.join(reference_patterns.get('p_class', []))}
            - List classes: {', '.join(reference_patterns.get('ul_class', []) + reference_patterns.get('ol_class', []))}
            - Table classes: {', '.join(reference_patterns.get('table_class', []))}
            
            APPLY THESE CLASSES TO THE HTML ELEMENTS YOU GENERATE.
            Example: <h2 class="{(reference_patterns.get('h2_class') or [''])[0]}">Heading</h2>
            """
        
        prompt = f"""
        Write a comprehensive, SEO-optimized article based on this outline.
        
        Outline:
        {outline_str}
        
        Tone of Voice:
        {tov}
        
        Target Keywords (integrate naturally):
        {keywords_str}
        
        {links_instruction}
        
        {style_instructions}
        
        Format:
        - Use Markdown (## for H2, ### for H3).
        - Use bullet points and bold text for readability.
        - Do NOT include the H1 title in the body (it will be added separately).
        - Write in the language of the ToV (likely Ukrainian).
        
        CRITICAL CONTENT RULES:
        1. PROMOTE THE BRAND: Focus on the user's brand (if known) or generic benefits. DO NOT promote competitors (like Silpo, ATB, Rozetka) unless explicitly comparing.
        2. IMAGES: You MUST include at least 2-3 image placeholders using the format: <img src="placeholder.jpg" alt="Descriptive alt text about the section">.
        3. SCHEMA: You do not need to generate JSON-LD, it will be added later.
        """
        
        response = self.ai_handler.generate_content(prompt)
        return response.text

    def rewrite_article(self, original_article, feedback, tov):
        """
        Rewrites an article based on specific feedback (e.g., SEO audit results).
        """
        prompt = f"""
        You are an expert SEO Editor. Your goal is to IMPROVE the article's SEO score without breaking existing optimizations.
        
        Original Article:
        {original_article}
        
        Feedback / Issues to Fix:
        {feedback}
        
        Tone of Voice:
        {tov}
        
        CRITICAL INSTRUCTIONS:
        1. **Preserve Keywords**: Do NOT remove existing keywords. Only ADD missing ones.
        2. **Fix Structure**: If the feedback mentions H1/H2/H3 issues, fix the hierarchy.
        3. **Minimal Changes**: Only change what is necessary to address the feedback. Do not rewrite the whole article if not needed.
        4. **Markdown Format**: Ensure the output is valid Markdown.
        5. **Internal Links**: Preserve any existing links.
        
        Return the FULL rewritten article in Markdown.
        """
        
        response = self.ai_handler.generate_content(prompt)
        return response.text
