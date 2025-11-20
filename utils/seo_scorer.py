import textstat
from bs4 import BeautifulSoup

def calculate_seo_score(html_content, target_keywords, tov_rules):
    """
    Calculates a 0-100 SEO score based on various metrics.
    """
    score = 0
    max_score = 100
    feedback = []

    soup = BeautifulSoup(html_content, 'html.parser')
    text_content = soup.get_text()

    # 1. Keyword Presence (30 points)
    found_keywords = []
    missing_keywords = []
    if target_keywords:
        for kw in target_keywords:
            if kw.lower() in text_content.lower():
                found_keywords.append(kw)
            else:
                missing_keywords.append(kw)
        
        kw_ratio = len(found_keywords) / len(target_keywords)
        score += 30 * kw_ratio
        if kw_ratio < 1.0:
            feedback.append(f"Missing keywords: {', '.join(missing_keywords)}")
    else:
        score += 30 # No keywords provided, assume pass
        feedback.append("No target keywords provided for scoring.")

    # 2. Readability (20 points)
    # Textstat often fails for Cyrillic. We'll use average sentence length as a proxy.
    sentences = [s for s in text_content.replace('!', '.').replace('?', '.').split('.') if len(s.strip()) > 5]
    if not sentences:
        avg_sentence_length = 0
    else:
        avg_sentence_length = len(text_content.split()) / len(sentences)
    
    # Optimal length: 10-20 words per sentence
    if 10 <= avg_sentence_length <= 25:
        score += 20
    elif avg_sentence_length < 10: # Too simple?
        score += 15
        feedback.append("Text might be too simple (short sentences).")
    else: # Too hard
        score += 10
        feedback.append(f"Text is hard to read (Avg {int(avg_sentence_length)} words/sentence). Aim for 15-20.")

    # 3. HTML Structure (30 points)
    # Check H1
    if len(soup.find_all('h1')) == 1:
        score += 10
    else:
        feedback.append("Document must have exactly one H1 tag.")
    
    # Check H2/H3 hierarchy
    h2s = soup.find_all('h2')
    if h2s:
        score += 10
    else:
        feedback.append("Document lacks H2 headings.")

    # Check Images/Alt
    imgs = soup.find_all('img')
    if imgs:
        missing_alt = [img for img in imgs if not img.get('alt')]
        if not missing_alt:
            score += 10
        else:
            score += 5
            feedback.append(f"{len(missing_alt)} images missing alt text.")
    else:
        feedback.append("No images found.")

    # 4. Schema Markup (20 points)
    if 'application/ld+json' in html_content:
        score += 20
    else:
        feedback.append("Missing Schema Markup (JSON-LD).")

    return {
        "score": int(score),
        "feedback": feedback,
        "readability_score": int(avg_sentence_length) if sentences else 0,
        "missing_keywords": missing_keywords
    }
