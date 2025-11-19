import os
import google.generativeai as genai
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import requests

class Strategist:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

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
                    print(f"Playwright launch failed: {e}. Installing browsers...")
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
                        print(f"Playwright failed for {url}: {e}")
                        # Fallback to Requests inside loop
                        self._scrape_fallback(url, outlines)
                browser.close()
                
        except Exception as e:
            print(f"Playwright crashed completely: {e}")
            # Fallback for all URLs if browser fails entirely
            for url in urls:
                 self._scrape_fallback(url, outlines)

        return outlines

    def _scrape_fallback(self, url, outlines_list):
        """Fallback scraper using requests."""
        try:
            print(f"Falling back to requests for {url}")
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
            print(f"Requests fallback failed for {url}: {e}")
            outlines_list.append({
                "url": url,
                "h1": "Error scraping",
                "structure": [f"Error: {str(e)}"]
            })

    def _generate_with_retry(self, prompt, max_retries=3):
        """Helper to generate content with retry logic for 429 errors."""
        for attempt in range(max_retries):
            try:
                return self.model.generate_content(prompt)
            except Exception as e:
                if "429" in str(e) or "Resource exhausted" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        print(f"⚠️ Rate limit hit. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                raise e

    def analyze_serp(self, topic):
        """
        Analyzes SERP for intent and features.
        """
        print(f"Analyzing SERP for: {topic}")
        results = []
        
        # Attempt 1: Playwright (Google) - Stealth Mode
        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                except Exception as e:
                    print(f"Playwright launch failed: {e}. Installing browsers...")
                    os.system("playwright install chromium")
                    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                print(f"Attempt 1: Scraping Google for: {topic}")
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
                    print(f"Google scrape failed: {e}")

                browser.close()
        except Exception as e:
            print(f"Playwright Google failed: {e}")

        # Attempt 2: Requests (DuckDuckGo HTML) - Very Robust Fallback
        if not results:
            print("Attempt 2: Using DuckDuckGo HTML (Requests)...")
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
                print(f"DDG Requests failed: {e}")

        # Attempt 3: Simulation (Last Resort)
        if not results:
            print("All scraping failed. Returning empty list to trigger manual input or retry.")
            # Do NOT return fake data anymore, it confuses the user.
            # Let's return a specific error-like result so the UI can show a warning but not fake info.
            results = [] 


        # Analyze Intent with Gemini
        prompt = f"Analyze the search intent for the topic '{topic}' in the context of Ukrainian Google Search. Return JSON with keys: 'intent' (Informational/Commercial/Transactional - translate to Ukrainian), 'features' (list of likely SERP features e.g. 'Відео', 'Сніпет', 'Картинки')."
        response = self._generate_with_retry(prompt)
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
                print(f"Playwright launch failed: {e}. Installing browsers...")
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
                    print(f"Error scraping {url}: {e}")
            browser.close()
        return outlines

    def extract_entities(self, text_content):
        """
        Uses Gemini to extract entities.
        """
        prompt = f"Extract key entities (products, ingredients, brands, technical terms) from the following text. Return as a JSON list of strings.\n\nText: {text_content[:2000]}"
        response = self._generate_with_retry(prompt)
        try:
            return json.loads(response.text.replace('```json', '').replace('```', ''))
        except:
            return []

    def suggest_faq(self, topic):
        """
        Generates FAQ questions based on the topic.
        """
        prompt = f"Generate 5 relevant FAQ questions for the topic '{topic}' that users might ask on Google. Return as a JSON list of strings."
        response = self._generate_with_retry(prompt)
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
                print(f"ToV Scraping failed: {e}")
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
                    print(f"Error parsing {doc['name']}: {e}")
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
        
        print(f"Generating ToV for {brand_name}...")
        response = self._generate_with_retry(prompt)
        print(f"ToV Generated (Length: {len(response.text)})")
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
        
        print(f"Refining ToV...")
        response = self._generate_with_retry(prompt)
        print(f"ToV Refined (Length: {len(response.text)})")
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
                print(f"Audience scraping failed: {e}")
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
        
        print(f"Generating {num_personas} personas for {brand_name}...")
        response = self.model.generate_content(prompt)
        print(f"Personas Generated (Length: {len(response.text)})")
        return response.text
