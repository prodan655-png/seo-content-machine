# SEO Content Machine - Walkthrough

## Overview
You have successfully built a professional-grade AI SEO tool tailored for OpenCart/Weblium. This tool automates research, content creation, and HTML generation while keeping you in control.

## 1. Setup
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
2.  **Environment Variables**:
    - Rename `.env.example` to `.env`.
    - Add your `GEMINI_API_KEY`.

## 2. Running the App
Run the Streamlit app from the `SEO_Machine` directory:
```bash
streamlit run app.py
```

## 3. Workflow Guide

### Step 1: Create a Project
- Go to the Sidebar.
- Select "Create New..." and enter a brand name (e.g., "Pervak").
- This creates a folder in `projects/Pervak/` with templates for ToV and Products.

### Step 2: Research (The Strategist)
- Navigate to the **Research** page.
- Enter a topic (e.g., "Whisky Yeast").
- Click **Analyze SERP**.
- The agent will use Playwright to scrape competitors and Gemini to analyze intent.
- Review the **Competitor Outlines** to see what you're up against.

### Step 3: Write (The Writer)
- Navigate to the **Write** page.
- Click **Generate Outline**.
- **Human-in-the-Loop**: Edit the JSON outline directly in the UI. Add sections, remove fluff.
- Enter target keywords.
- Click **Write Article**. The AI will draft the content using your ToV.

### Step 4: Code & Export (The Coder)
- The tool automatically converts the Markdown to HTML.
- **Internal Linking**: It scans your Vector DB (if populated via Sitemap) for link opportunities.
- **Asset Matching**: It fuzzy-matches keywords to images in your `assets/` folder.
- **SEO Score**: Check the score (0-100) and fix any issues.
- Download the final HTML.

## 4. Pro Tips
- **Sitemap Ingestion**: Go to the Dashboard and paste your sitemap URL to populate the Vector DB for internal linking.
- **Assets**: Upload images in the Settings tab. Name them descriptively (e.g., `yeast_turbo_100g.jpg`) for the fuzzy matcher to find them.
- **Reference HTML**: Replace `projects/{brand}/reference.html` with a snippet of your best article to teach the Coder your preferred HTML structure.
