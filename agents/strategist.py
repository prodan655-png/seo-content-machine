import os
from utils.ai_handler import AIHandler
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import requests
import time
import random

class Strategist:
    def __init__(self, api_key):
        self.ai_handler = AIHandler(api_key, model_name="gemini-2.5-flash")

    # ... (previous methods) ...

    def analyze_competitors(self, urls):
        """
        Scrapes competitor URLs to extract outlines (H1-H3).
        """
        outlines = []
        
        # Try Playwright first
        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True)
                except Exception as e:
                    # print(f"Playwright launch failed: {e}. Installing browsers...")
                    pass
                    os.system("playwright install chromium")
                    browser = p.chromium.launch(headless=True)
                
                for url in urls:
                    try:
                        page = browser.new_page()
                        page.goto(url, timeout=15000)
                        content = page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        h1 = soup.find('h1').get_text().strip() if soup.find('h1') else "No H1"
                        headings = [h.get_text().strip() for h in soup.find_all(['h2', 'h3'])]
                        
                        outlines.append({
                            "url": url,
                            "h1": h1,
                            "structure": headings[:10] # Limit to top 10 headings
                        })
                        page.close()
                    except Exception as e:
                        # print(f"Playwright failed for {url}: {e}")
                        # Fallback to Requests inside loop
                        self._scrape_fallback(url, outlines)
                browser.close()
                
        except Exception as e:
            # print(f"Playwright crashed completely: {e}")
            # Fallback for all URLs if browser fails entirely
            for url in urls:
                 self._scrape_fallback(url, outlines)

        return outlines

    def _scrape_fallback(self, url, outlines_list):
        """Fallback scraper using requests."""
        try:
            # print(f"Falling back to requests for {url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            h1 = soup.find('h1').get_text().strip() if soup.find('h1') else "No H1 (Requests)"
            headings = [h.get_text().strip() for h in soup.find_all(['h2', 'h3'])]
            
            outlines_list.append({
                "url": url,
                "h1": h1,
                "structure": headings[:10]
            })
        except Exception as e:
            # print(f"Requests fallback failed for {url}: {e}")
            outlines_list.append({
                "url": url,
                "h1": "Error scraping",
                "structure": [f"Error: {str(e)}"]
            })

    def generate_topic_ideas(self, niche, num_topics=10, context_data=None):
        """
        Generates topic ideas for a given niche, optionally using context (competitors/sitemap).
        
        Args:
            niche: The niche/industry
            num_topics: Number of topics
            context_data: Optional string containing competitor headers or sitemap titles
        """
        context_prompt = ""
        if context_data:
            context_prompt = f"Based on the following competitor/existing content analysis:\n{context_data[:5000]}\n\n"

        prompt = f"""
        You are an SEO content strategist. Generate {num_topics} article topic ideas for the niche: "{niche}".
        
        {context_prompt}
        
        Requirements:
        - Topics should be SEO-friendly and address user search intent
        - Mix informational, commercial, and transactional intents
        - Include long-tail keywords where appropriate
        - Make titles compelling and click-worthy
        - Write in Ukrainian language
        
        Return as JSON array with format:
        [
            {{"title": "Topic Title", "description": "Brief description of what the article would cover"}}
        ]
        
        JSON ONLY. NO MARKDOWN.
        """
        
        try:
            response = self.ai_handler.generate_content(prompt)
            topics = json.loads(response.text.replace('```json', '').replace('```', ''))
            return topics if isinstance(topics, list) else []
        except Exception as e:
            return [{"title": f"Тема {i+1} для {niche}", "description": "Опис недоступний"} for i in range(num_topics)]

    def generate_keywords(self, topic, num_keywords=20):
        """
        Generates SEO keywords for a topic.
        """
        prompt = f"""
        Generate {num_keywords} SEO keywords for the topic: "{topic}".
        Include a mix of:
        - Head terms (high volume)
        - Long-tail keywords (specific intent)
        - LSI keywords (semantically related)
        
        Return as a JSON list of objects:
        [
            {{"keyword": "keyword 1", "type": "Head"}},
            {{"keyword": "keyword 2", "type": "Long-tail"}},
            ...
        ]
        
        Language: Ukrainian.
        JSON ONLY.
        """
        try:
            response = self.ai_handler.generate_content(prompt)
            return json.loads(response.text.replace('```json', '').replace('```', ''))
        except:
            return [{"keyword": topic, "type": "Head"}]




    def analyze_serp(self, topic):
        """
        Analyzes SERP for intent and features.
        """
        # print(f"Analyzing SERP for: {topic}")
        results = []
        
        # Attempt 1: Playwright (Google) - Stealth Mode
        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                except Exception as e:
                    # print(f"Playwright launch failed: {e}. Installing browsers...")
                    os.system("playwright install chromium")
                    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # print(f"Attempt 1: Scraping Google for: {topic}")
                try:
                    page.goto(f"https://www.google.com/search?q={topic}", timeout=10000)
                    page.wait_for_load_state("domcontentloaded")
                    
                    links = page.query_selector_all('div.g h3') # Standard Google selector
                    for h3 in links[:5]:
                        try:
                            parent_a = h3.xpath('..')[0]
                            url = parent_a.get_attribute('href')
                            title = h3.inner_text()
                            if url and title and url.startswith('http'):
                                results.append({"url": url, "title": title})
                        except:
                            continue
                except Exception as e:
                    # print(f"Google scrape failed: {e}")
                    pass

                browser.close()
        except Exception as e:
            # print(f"Playwright Google failed: {e}")
            pass

        # Attempt 2: Requests (DuckDuckGo HTML) - Very Robust Fallback
        if not results:
            # print("Attempt 2: Using DuckDuckGo HTML (Requests)...")
            try:
                import requests
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Referer": "https://duckduckgo.com/"
                }
                # DDG HTML version doesn't require JS
                resp = requests.post("https://html.duckduckgo.com/html/", data={'q': topic}, headers=headers, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    # DDG HTML selectors
                    for link in soup.find_all('a', class_='result__a')[:5]:
                        url = link.get('href')
                        title = link.get_text(strip=True)
                        if url and title:
                            results.append({"url": url, "title": title})
            except Exception as e:
                # print(f"DDG Requests failed: {e}")
                pass

        # Attempt 3: Simulation (Last Resort)
        if not results:
            # print("All scraping failed. Returning empty list to trigger manual input or retry.")
            # Do NOT return fake data anymore, it confuses the user.
            # Let's return a specific error-like result so the UI can show a warning but not fake info.
            results = [] 


        # Analyze Intent with Gemini
        prompt = f"Analyze the search intent for the topic '{topic}' in the context of Ukrainian Google Search. Return JSON with keys: 'intent' (Informational/Commercial/Transactional - translate to Ukrainian), 'features' (list of likely SERP features e.g. 'Відео', 'Сніпет', 'Картинки')."
        response = self.ai_handler.generate_content(prompt)
        try:
            analysis = json.loads(response.text.replace('```json', '').replace('```', ''))
        except:
            analysis = {"intent": "Informational", "features": []}

        return {
            "topic": topic,
            "competitors": results,
            "intent": analysis.get("intent"),
            "serp_features": analysis.get("features")
        }

    def analyze_competitors(self, urls):
        """
        Scrapes competitor URLs to extract outlines (H1-H3).
        """
        outlines = []
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as e:
                # print(f"Playwright launch failed: {e}. Installing browsers...")
                os.system("playwright install chromium")
                browser = p.chromium.launch(headless=True)
            for url in urls:
                try:
                    page = browser.new_page()
                    page.goto(url, timeout=15000)
                    content = page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    h1 = soup.find('h1').get_text(strip=True) if soup.find('h1') else "No H1"
                    headings = []
                    for h in soup.find_all(['h2', 'h3']):
                        headings.append(f"{h.name.upper()}: {h.get_text(strip=True)}")
                    
                    outlines.append({
                        "url": url,
                        "h1": h1,
                        "structure": headings[:10] # Limit for brevity
                    })
                    page.close()
                except Exception as e:
                    # print(f"Error scraping {url}: {e}")
                    pass
            browser.close()
        return outlines

    def extract_entities(self, text_content):
        """
        Uses Gemini to extract entities.
        """
        prompt = f"Extract key entities (products, ingredients, brands, technical terms) from the following text. Return as a JSON list of strings.\n\nText: {text_content[:2000]}"
        response = self.ai_handler.generate_content(prompt)
        try:
            return json.loads(response.text.replace('```json', '').replace('```', ''))
        except:
            return []

    def suggest_faq(self, topic):
        """
        Generates FAQ questions based on the topic.
        """
        prompt = f"Generate 5 relevant FAQ questions for the topic '{topic}' that users might ask on Google. Return as a JSON list of strings."
        response = self.ai_handler.generate_content(prompt)
        try:
            return json.loads(response.text.replace('```json', '').replace('```', ''))
        except:
            return [f"What is {topic}?", f"How to use {topic}?"]

    def generate_tov(self, brand_name, industry, url=None, emotional_tone="Нейтральний", formality_level="Нейтральний", unique_trait="", uploaded_docs=None):
        """
        Generates a Tone of Voice description based on brand info and optional URL scraping.
        """
        context = ""
        if url:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, timeout=15000)
                    # Get text from home page
                    text = page.inner_text('body')[:5000] # Limit text
                    context = f"Контент сайту:\n{text}\n\n"
                    browser.close()
            except Exception as e:
                # print(f"ToV Scraping failed: {e}")
                context = "Could not scrape website. "
        
        # Add uploaded documents context
        if uploaded_docs:
            # No need to import parser here, text is already extracted in app.py
            docs_context = "\n\nДодаткові матеріали про бренд:\n"
            for doc in uploaded_docs[:3]:  # Limit to 3 docs
                try:
                    # Check if content is already text (new optimization) or bytes (old way)
                    if doc.get('is_text', False):
                        text = doc['content']
                    else:
                        # Fallback for backward compatibility
                        from utils.document_parser import extract_text_from_document
                        text = extract_text_from_document(doc['content'], doc['type'])
                        
                    docs_context += f"\n--- {doc['name']} ---\n{text[:5000]}\n"  # Increased limit to 5000 chars
                except Exception as e:
                    # print(f"Error parsing {doc['name']}: {e}")
                    pass
            context += docs_context

        prompt = f"""
        Ти - експерт з брендингу. Створи детальний гайд Tone of Voice (Голос Бренду) для бренду.
        
        ВАЖЛИВО: Вся відповідь ОБОВ'ЯЗКОВО має бути УКРАЇНСЬКОЮ мовою!
        
        ІНФОРМАЦІЯ ПРО БРЕНД:
        - Назва бренду: {brand_name}
        - Індустрія: {industry}
        - Емоційний тон: {emotional_tone}
        - Рівень формальності: {formality_level}
        - Унікальна риса: {unique_trait if unique_trait else "не вказано"}
        {context}
        
        Створи Markdown гайд, який включає:
        
        ## 1. Основні цінності
        - 3-5 ключових цінностей бренду (маркований список)
        
        ## 2. Характеристики голосу
        - 5-7 конкретних характеристик (маркований список)
        - Враховуй обраний емоційний тон ({emotional_tone}) та формальність ({formality_level})
        
        ## 3. Що робити
        - 5+ конкретних рекомендацій для комунікації
        
        ## 4. Чого НЕ робити (Червоні прапорці)
        - 5+ конкретних речей, яких слід уникати
        - Фрази, які НІКОЛИ не використовувати
        
        ## 5. Приклади фраз (мінімум 10)
        Створи конкретні приклади для різних ситуацій:
        - Заголовки продуктів (2 приклади)
        - Описи категорій (2 приклади)
        - Email розсилки (2 приклади)
        - Соцмережі (2 приклади)
        - Обробка заперечень (2 приклади)
        
        Кожен приклад має бути у форматі:
        **Ситуація:** [опис]
        **Фраза:** "[конкретна фраза українською]"
        
        КРИТИЧНО ВАЖЛИВО: 
        - НЕ використовуй таблиці! Тільки маркованi списки.
        - Вся відповідь має бути УКРАЇНСЬКОЮ мовою (включно з заголовками)!
        - Будь максимально конкретним, не загальним.
        - Враховуй унікальну рису бренду: {unique_trait if unique_trait else "створи унікальний стиль"}
        - Якщо є додаткові матеріали, ОБОВ'ЯЗКОВО посилайся на них (наприклад: "Згідно з вашою стратегією...", "Як зазначено в дослідженні...").
        - Якщо матеріали суперечать один одному, надавай пріоритет завантаженим документам.
        """
        
        # print(f"Generating ToV for {brand_name}...")
        response = self.ai_handler.generate_content(prompt)
        # print(f"ToV Generated (Length: {len(response.text)})")
        return response.text

    def refine_tov(self, current_tov, instructions):
        """
        Refines the existing ToV based on user instructions.
        """
        prompt = f"""
        Act as a Brand Strategist. Refine the following Tone of Voice guide based on the user's instructions.
        
        Current ToV:
        {current_tov}
        
        User Instructions:
        {instructions}
        
        Output the updated ToV in Markdown. Keep the same structure if possible, but apply the requested changes. Language: Ukrainian.
        """
        
        # print(f"Refining ToV...")
        response = self.ai_handler.generate_content(prompt)
        # print(f"ToV Refined (Length: {len(response.text)})")
        return response.text

    def generate_audience(self, brand_name, industry, url=None, business_model="B2C", num_personas=2):
        """
        Generates detailed target audience personas with Jobs-to-be-Done framework.
        """
        context = ""
        if url:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, timeout=15000)
                    text = page.inner_text('body')[:5000]
                    context = f"Контент сайту:\n{text}\n\n"
                    browser.close()
            except Exception as e:
                # print(f"Audience scraping failed: {e}")
                context = ""

        # Extract business model type
        if "B2B" in business_model and "B2C" in business_model:
            biz_type = "B2B та B2C"
        elif "B2B" in business_model:
            biz_type = "B2B (бізнес для бізнесу)"
        else:
            biz_type = "B2C (бізнес для споживачів)"

        prompt = f"""
        Ти - експерт з маркетингу. Створи {num_personas} детальні персони для бренду.
        
        ВАЖЛИВО: Вся відповідь ОБОВ'ЯЗКОВО має бути УКРАЇНСЬКОЮ мовою!
        
        ІНФОРМАЦІЯ ПРО БРЕНД:
        - Назва бренду: {brand_name}
        - Індустрія: {industry}
        - Тип бізнесу: {biz_type}
        {context}
        
        Створи {num_personas} РІЗНІ персони. Кожна персона має бути УНІКАЛЬНОЮ та КОНКРЕТНОЮ.
        
        ДЛЯ КОЖНОЇ ПЕРСОНИ створи такий Markdown розділ:
        
        ## Персона [Номер]: [Українське ім'я] - [Роль/Посада]
        
        ### 👤 Демографія
        - **Вік:** [конкретний діапазон]
        - **Стать:** [стать]
        - **Локація:** [місто/регіон України]
        - **Освіта:** [рівень освіти]
        - **Дохід:** [рівень доходу]
        - **Сімейний стан:** [стан]
        
        ### 🧠 Психографія
        - **Цінності:** [3-4 ключові цінності]
        - **Інтереси:** [хобі, захоплення]
        - **Стиль життя:** [опис повсякденного життя]
        - **Улюблені бренди:** [2-3 бренди, які вони люблять]
        - **Медіа:** [де шукають інформацію - соцмережі, блоги, YouTube тощо]
        
        ### 🎯 Jobs-to-be-Done
        - **Функціональна робота:** [що конкретно хочуть зробити/досягти]
        - **Емоційна робота:** [як хочуть відчувати себе]
        - **Соціальна робота:** [як хочуть виглядати в очах інших]
        
        ### 💔 Болі та бар'єри
        - [Біль 1: конкретна проблема]
        - [Біль 2: конкретна проблема]
        - [Біль 3: конкретна проблема]
        - **Головний бар'єр до покупки:** [що заважає купити]
        
        ### 🚀 Тригери та мотиватори
        - **Що змушує шукати рішення:** [конкретна ситуація]
        - **Критерії вибору:** [топ-3 критерії при виборі продукту]
        - **Що впливає на рішення:** [хто/що впливає на вибір]
        
        ### 🛒 Customer Journey
        - **Усвідомлення:** [як дізнається про проблему]
        - **Розгляд:** [як порівнює варіанти, що гуглить]
        - **Рішення:** [що остаточно впливає на вибір]
        - **Покупка:** [де та як купує]
        
        ### 💬 Цитата персони
        "[Реалістична цитата українською мовою, яка відображає їх думки, болі та мотивацію. 2-3 речення.]"
        
        ---
        
        КРИТИЧНО ВАЖЛИВО:
        - Кожна персона має бути РІЗНОЮ (різний вік, стать, потреби)
        - Використовуй УКРАЇНСЬКІ імена
        - Будь максимально КОНКРЕТНИМ (не "25-45 років", а "32-38 років")
        - Цитати мають звучати ПРИРОДНО та РЕАЛІСТИЧНО
        - Враховуй тип бізнесу ({biz_type})
        - Вся відповідь УКРАЇНСЬКОЮ мовою!
        """
        
        # print(f"Generating {num_personas} personas for {brand_name}...")
        response = self.ai_handler.generate_content(prompt)
        # print(f"Personas Generated (Length: {len(response.text)})")
        return response.text

    def generate_cjm(self, brand_name, industry, personas_text):
        """
        Generates a Customer Journey Map (CJM) in Markdown table format.
        """
        prompt = f"""
        Ти - експерт з Customer Experience. Створи Customer Journey Map (CJM) для бренду.
        
        БРЕНД: {brand_name} ({industry})
        
        ПЕРСОНИ (АУДИТОРІЯ):
        {personas_text[:3000]}... (скорочено)
        
        ЗАВДАННЯ:
        Створи CJM у вигляді Markdown таблиці.
        
        Етапи (Стовпці):
        1. Усвідомлення (Awareness)
        2. Розгляд (Consideration)
        3. Придбання (Purchase)
        4. Утримання (Retention)
        5. Адвокація (Advocacy)
        
        Виміри (Рядки):
        - Цілі клієнта (User Goals)
        - Точки контакту (Touchpoints)
        - Емоції (Emotions - використовуй емодзі)
        - Бар'єри (Barriers)
        - Можливості для бренду (Opportunities)
        
        ВАЖЛИВО:
        - Відповідь має містити ТІЛЬКИ Markdown таблицю.
        - Мова: УКРАЇНСЬКА.
        - Будь конкретним для цієї ніші.
        """
        
        # print(f"Generating CJM for {brand_name}...")
        response = self.ai_handler.generate_content(prompt)
        # print(f"CJM Generated (Length: {len(response.text)})")
        return response.text

    def analyze_competitor_tov(self, url):
        """
        Analyzes a competitor's website to extract their Tone of Voice.
        Returns a JSON object with emotional_tone, formality_level, unique_trait, values.
        """
        # print(f"Analyzing Competitor ToV: {url}")
        text_content = ""
        
        # 1. Scrape Content (Robust Method)
        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True)
                except:
                    os.system("playwright install chromium")
                    browser = p.chromium.launch(headless=True)
                
                try:
                    page = browser.new_page()
                    page.goto(url, timeout=15000)
                    text_content = page.inner_text('body')[:10000] # Get more text for analysis
                    page.close()
                except Exception as e:
                    # print(f"Playwright failed for {url}: {e}")
                    # Fallback to Requests
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                        resp = requests.get(url, headers=headers, timeout=10)
                        soup = BeautifulSoup(resp.content, 'html.parser')
                        text_content = soup.get_text(separator=' ', strip=True)[:10000]
                    except Exception as e2:
                        # print(f"Requests fallback failed: {e2}")
                        return {"error": "Could not scrape website"}
                finally:
                    browser.close()
        except Exception as e:
            # print(f"Scraping crashed: {e}")
            return {"error": str(e)}

        if not text_content:
            return {"error": "Empty content"}

        # 2. Analyze with AI
        prompt = f"""
        Analyze the text from a competitor's website and extract their Tone of Voice (ToV) characteristics.
        
        TEXT:
        {text_content[:5000]}...
        
        TASK:
        Return a JSON object with the following keys (values must be in UKRAINIAN):
        - "emotional_tone": Choose ONE from: ["Нейтральний", "Дружній", "Серйозний", "Веселий", "Натхненний", "Експертний"]
        - "formality_level": Choose ONE from: ["Дуже офіційний", "Офіційний", "Середній", "Нейтральний", "Дружній", "Дуже дружній"]
        - "unique_trait": (e.g., "Використання сленгу", "Науковий підхід", "Гумор", "Мінімалізм")
        - "values": (list of 3 key values inferred from text)
        
        JSON ONLY. NO MARKDOWN.
        """
        
        response = self.ai_handler.generate_content(prompt)
        try:
            return json.loads(response.text.replace('```json', '').replace('```', ''))
        except:
            return {
                "emotional_tone": "Не визначено",
                "formality_level": "Не визначено",
                "unique_trait": "Не визначено",
                "values": []
            }
