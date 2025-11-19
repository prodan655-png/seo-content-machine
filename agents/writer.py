import google.generativeai as genai
import json

class Writer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

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
        response = self.model.generate_content(prompt)
        try:
            return json.loads(response.text.replace('```json', '').replace('```', ''))
        except Exception as e:
            print(f"Error parsing outline JSON: {e}")
            # Fallback outline
            return {
                "title": f"Guide to {research_data['topic']}",
                "sections": [{"heading": "Introduction", "subheadings": [], "notes": "Intro"}],
                "faq": []
            }

    def write_article(self, outline, tov, keywords):
        """
        Generates the full article content based on the approved outline.
        """
        outline_str = json.dumps(outline, indent=2)
        keywords_str = ", ".join(keywords)
        
        prompt = f"""
        Write a comprehensive, SEO-optimized article based on this outline.
        
        Outline:
        {outline_str}
        
        Tone of Voice:
        {tov}
        
        Target Keywords (integrate naturally):
        {keywords_str}
        
        Format:
        - Use Markdown (## for H2, ### for H3).
        - Use bullet points and bold text for readability.
        - Do NOT include the H1 title in the body (it will be added separately).
        - Write in the language of the ToV (likely Ukrainian).
        """
        
        response = self.model.generate_content(prompt)
        return response.text
