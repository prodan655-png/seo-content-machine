import streamlit as st
import os
import asyncio
import sys
from dotenv import load_dotenv
import pandas as pd

# Fix for Windows Asyncio Loop (Playwright compatibility)
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from utils.file_manager import FileManager
from utils.vector_db import VectorDB
from utils.sitemap_parser import ingest_sitemap
from utils.seo_scorer import calculate_seo_score

from agents.strategist import Strategist
from agents.writer import Writer
from agents.coder import Coder

# Load Env
# Load Env
load_dotenv()

# Try to get API Key from multiple sources
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY and "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]

# Clean API Key (remove quotes if user added them in secrets)
if API_KEY:
    API_KEY = API_KEY.strip().strip('"').strip("'")

# Initialize Utils
file_manager = FileManager()
vector_db = VectorDB()
strategist = Strategist(API_KEY) if API_KEY else None
writer = Writer(API_KEY) if API_KEY else None
coder = Coder(vector_db)

# Page Config
st.set_page_config(page_title="SEO Content Machine", layout="wide", page_icon="🚀")

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; }
    h1 { color: #2E4053; }
    .stButton button { width: 100%; border-radius: 8px; }
    .stMetric { background-color: #F4F6F7; padding: 10px; border-radius: 8px; }
    .css-1d391kg { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & NAVIGATION ---
# --- SIDEBAR & NAVIGATION ---
st.sidebar.title("🚀 SEO Machine")

# Project Selection Logic
projects = file_manager.list_projects()

# Session State for Project Selection
if 'selected_project' not in st.session_state:
    st.session_state['selected_project'] = projects[0] if projects else None

# Project Selector
project_options = ["Create New..."] + projects
# Find index of current selection
try:
    index = project_options.index(st.session_state['selected_project']) if st.session_state['selected_project'] in project_options else 0
except ValueError:
    index = 0

selected_option = st.sidebar.selectbox("Select Project", project_options, index=index)

if selected_option == "Create New...":
    st.title("✨ Створення Нового Проекту")
    
    # Initialize Wizard State
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1
    if 'new_project_data' not in st.session_state:
        st.session_state.new_project_data = {}

    # Wizard Progress
    steps = ["Бренд", "Tone of Voice", "Аудиторія", "Фініш"]
    current_step = st.session_state.wizard_step
    st.progress(current_step / len(steps))
    
    # Step 1: Brand Identity
    if current_step == 1:
        st.subheader("Крок 1: Ідентифікація Бренду")
        
        # Direct widgets (No Form) to allow dynamic "Other" field
        brand_name = st.text_input("Назва Бренду", value=st.session_state.new_project_data.get('brand_name', ''))
        website_url = st.text_input("URL Сайту", value=st.session_state.new_project_data.get('website_url', ''))
        
        industry_selection = st.selectbox("Ніша / Індустрія", ["E-commerce", "SaaS", "Blog", "Local Business", "Other"], index=0)
        custom_industry = ""
        if industry_selection == "Other":
            custom_industry = st.text_input("Вкажіть вашу нішу", value=st.session_state.new_project_data.get('custom_industry', ''))
        
        # Document Upload Section
        st.divider()
        st.markdown("### 📄 Додаткові матеріали (опціонально)")
        st.info("Завантажте документи про ваш бренд (дослідження аудиторії, SMM стратегії, брендбук тощо). ШІ використає їх для кращої генерації ToV та персон.")
        
        uploaded_files = st.file_uploader(
            "Завантажити документи",
            type=["pdf", "docx", "txt", "md", "pptx"],
            accept_multiple_files=True,
            help="Підтримуються формати: PDF, DOCX, TXT, MD, PPTX"
        )
        
        # Initialize uploaded_docs in session state
        if 'uploaded_docs' not in st.session_state.new_project_data:
            st.session_state.new_project_data['uploaded_docs'] = []
        
        if uploaded_files:
            # Import parser here to avoid circular imports if placed at top
            from utils.document_parser import extract_text_from_document
            
            st.session_state.new_project_data['uploaded_docs'] = []
            
            for uploaded_file in uploaded_files:
                with st.spinner(f"Обробляю файл {uploaded_file.name}..."):
                    try:
                        # Read file content
                        file_content = uploaded_file.read()
                        
                        # Extract text immediately to save memory
                        extracted_text = extract_text_from_document(file_content, uploaded_file.type)
                        
                        # Store ONLY the text and metadata, NOT the binary content
                        st.session_state.new_project_data['uploaded_docs'].append({
                            'name': uploaded_file.name,
                            'content': extracted_text, # Storing text, not bytes
                            'type': uploaded_file.type,
                            'is_text': True # Flag to indicate this is already parsed text
                        })
                    except Exception as e:
                        st.error(f"Помилка обробки файлу {uploaded_file.name}: {e}")
            
            st.success(f"✅ Оброблено {len(uploaded_files)} файл(ів)")
            
            # Show uploaded files
            with st.expander("Переглянути завантажені файли"):
                for doc in st.session_state.new_project_data['uploaded_docs']:
                    st.text(f"📄 {doc['name']} ({len(doc['content'])} символів)")
        
        st.divider()
        
        if st.button("Далі ➡️", type="primary"):
            final_industry = custom_industry if industry_selection == "Other" else industry_selection
            
            if brand_name:
                if industry_selection == "Other" and not custom_industry:
                    st.error("Будь ласка, вкажіть вашу нішу!")
                else:
                    st.session_state.new_project_data.update({
                        'brand_name': brand_name,
                        'website_url': website_url,
                        'industry': final_industry,
                        'custom_industry': custom_industry # Save for UI persistence
                    })
                    st.session_state.wizard_step = 2
                    st.rerun()
            else:
                st.error("Введіть назву бренду!")


    # Step 2: Tone of Voice
    elif current_step == 2:
        st.subheader("Крок 2: Tone of Voice (Голос Бренду)")
        st.info("Опишіть, як ваш бренд спілкується з клієнтами. (Дружній, Офіційний, Експертний...)")
        
        # CRITICAL: Initialize widget state FIRST, before any buttons
        if 'tov_editor' not in st.session_state:
            st.session_state['tov_editor'] = st.session_state.new_project_data.get('tov', '')
        
        # Pre-generation configuration
        with st.expander("⚙️ Налаштування генерації", expanded=True):
            st.markdown("**Допоможіть ШІ створити ідеальний ToV для вашого бренду:**")
            
            col1, col2 = st.columns(2)
            with col1:
                emotional_tone = st.radio(
                    "Емоційний тон",
                    ["Серйозний", "Веселий", "Натхненний", "Експертний"],
                    key="emotional_tone_selector",
                    help="Яка емоція має домінувати у вашому контенті?"
                )
            
            with col2:
                formality_level = st.select_slider(
                    "Рівень формальності",
                    options=["Дуже офіційний", "Офіційний", "Нейтральний", "Дружній", "Дуже дружній"],
                    value="Нейтральний",
                    help="Наскільки формально ви спілкуєтесь з клієнтами?"
                )
            
            unique_trait = st.text_input(
                "Унікальна риса бренду",
                placeholder="напр. 'Ми єдині, хто використовує органічні інгредієнти' або 'Працюємо 24/7'",
                help="Що робить ваш бренд особливим?"
            )
            
            # Save to session state
            st.session_state.new_project_data.update({
                'emotional_tone': emotional_tone,
                'formality_level': formality_level,
                'unique_trait': unique_trait
            })
        
        # AI Generator & Refiner
        col_gen, col_refine = st.columns([1, 2])
        with col_gen:
            if st.button("✨ Створити з нуля (ШІ)"):
                if not API_KEY:
                    st.error("⚠️ API Key не знайдено!")
                else:
                    with st.spinner("Аналізую бренд..."):
                        try:
                            brand_name = st.session_state.new_project_data.get('brand_name')
                            industry = st.session_state.new_project_data.get('industry')
                            url = st.session_state.new_project_data.get('website_url')
                            emotional_tone = st.session_state.new_project_data.get('emotional_tone', 'Нейтральний')
                            formality_level = st.session_state.new_project_data.get('formality_level', 'Нейтральний')
                            unique_trait = st.session_state.new_project_data.get('unique_trait', '')
                            uploaded_docs = st.session_state.new_project_data.get('uploaded_docs', [])
                            
                            print(f"[DEBUG] Generating ToV for: {brand_name}, {industry}, {url}")
                            if uploaded_docs:
                                print(f"[DEBUG] Using {len(uploaded_docs)} uploaded documents")
                            st.write(f"🔍 Debug: Викликаю AI для {brand_name}...")
                            
                            generated_tov = strategist.generate_tov(
                                brand_name, 
                                industry, 
                                url,
                                emotional_tone=emotional_tone,
                                formality_level=formality_level,
                                unique_trait=unique_trait,
                                uploaded_docs=uploaded_docs
                            )
                            
                            print(f"[DEBUG] Generated ToV length: {len(generated_tov)}")
                            st.write(f"✅ Debug: Отримано {len(generated_tov)} символів")
                            
                            # Update both data and widget state
                            st.session_state.new_project_data['tov'] = generated_tov
                            st.session_state['tov_editor'] = generated_tov 
                            
                            print(f"[DEBUG] Session state updated. tov_editor length: {len(st.session_state['tov_editor'])}")
                            st.write(f"💾 Debug: Збережено в session_state")
                            
                            # Force re-render to show the text in the text_area
                            st.rerun()
                        except Exception as e:
                            st.error(f"Помилка: {e}")
                            print(f"[ERROR] {e}")
                            import traceback
                            traceback.print_exc()
        
        with col_refine:
            st.markdown("**💬 AI Copilot (Чат з ШІ)**")
            
            # Initialize chat history
            if 'tov_chat_history' not in st.session_state:
                st.session_state.tov_chat_history = []
            
            # Display chat history
            if st.session_state.tov_chat_history:
                with st.expander("📜 Історія змін", expanded=False):
                    for i, msg in enumerate(st.session_state.tov_chat_history):
                        st.markdown(f"**Ви:** {msg['user']}")
                        st.markdown(f"*ШІ:* {msg['ai'][:100]}...")
                        st.divider()
            
            # Chat input
            refine_instruction = st.text_input("Що змінити?", placeholder="напр. 'Зроби тон більш дружнім' або 'Прибери таблиці'", key="refine_input")
            if st.button("🛠️ Покращити ToV") and refine_instruction:
                current_tov = st.session_state.new_project_data.get('tov', '')
                if not current_tov:
                    st.warning("Спочатку напишіть або згенеруйте ToV!")
                else:
                    with st.spinner("Вношу правки..."):
                        try:
                            new_tov = strategist.refine_tov(current_tov, refine_instruction)
                            st.session_state.new_project_data['tov'] = new_tov
                            st.session_state['tov_editor'] = new_tov
                            
                            # Save to chat history
                            st.session_state.tov_chat_history.append({
                                'user': refine_instruction,
                                'ai': f"Оновлено ({len(new_tov)} символів)"
                            })
                            
                            # Force re-render to show updated text
                            st.rerun()
                        except Exception as e:
                            st.error(f"Помилка: {e}")

        # Manual Edit - widget is bound to session state via key
        tov = st.text_area("Опис ToV (можна редагувати вручну)", 
                            height=400,
                            key="tov_editor")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ Назад"):
                st.session_state.wizard_step = 1
                st.rerun()
        with c2:
            if st.button("Далі ➡️", type="primary"):
                # Save the value from the widget state
                st.session_state.new_project_data['tov'] = st.session_state.tov_editor
                st.session_state.wizard_step = 3
                st.rerun()

    # Step 3: Target Audience
    elif current_step == 3:
        st.subheader("Крок 3: Цільова Аудиторія")
        
        # Initialize widget state
        if 'audience_editor' not in st.session_state:
            st.session_state['audience_editor'] = st.session_state.new_project_data.get('audience', '')
        
        # Persona configuration
        with st.expander("⚙️ Налаштування персон", expanded=True):
            st.markdown("**Допоможіть ШІ створити детальні персони вашої аудиторії:**")
            
            col1, col2 = st.columns(2)
            with col1:
                business_model = st.radio(
                    "Тип бізнесу",
                    ["B2B (бізнес для бізнесу)", "B2C (бізнес для споживачів)", "Обидва (B2B + B2C)"],
                    help="Для кого ваш продукт/послуга?"
                )
            
            with col2:
                num_personas = st.select_slider(
                    "Кількість персон",
                    options=[1, 2, 3],
                    value=2,
                    help="Скільки різних типів клієнтів у вас є?"
                )
            
            # Save to session state
            st.session_state.new_project_data.update({
                'business_model': business_model,
                'num_personas': num_personas
            })
        
        # AI Generator
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✨ Згенерувати персони (ШІ)"):
                if not API_KEY:
                    st.error("⚠️ API Key не знайдено!")
                else:
                    with st.spinner(f"Створюю {num_personas} персони..."):
                        try:
                            brand_name = st.session_state.new_project_data.get('brand_name')
                            industry = st.session_state.new_project_data.get('industry')
                            url = st.session_state.new_project_data.get('website_url')
                            business_model = st.session_state.new_project_data.get('business_model', 'B2C')
                            num_personas = st.session_state.new_project_data.get('num_personas', 2)
                            
                            # Generate personas
                            personas_text = strategist.generate_audience(
                                brand_name, 
                                industry, 
                                url,
                                business_model=business_model,
                                num_personas=num_personas
                            )
                            st.session_state.new_project_data['audience'] = personas_text
                            st.session_state['audience_editor'] = personas_text
                            st.rerun()
                        except Exception as e:
                            st.error(f"Помилка: {e}")
        
        with col2:
            st.markdown(f"**💡 Підказка:** ШІ створить {num_personas} детальні персони з Jobs-to-be-Done")
        
        # Display personas
        st.divider()
        st.markdown("### Персони вашої аудиторії")
        
        # Manual edit with tabs for better organization
        audience = st.text_area(
            "Опис аудиторії (можна редагувати вручну)", 
            height=400,
            key="audience_editor",
            placeholder="Натисніть 'Згенерувати персони' або опишіть вашу цільову аудиторію вручну..."
        )
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ Назад"):
                st.session_state.wizard_step = 2
                st.rerun()
        with c2:
            if st.button("Далі ➡️", type="primary"):
                st.session_state.new_project_data['audience'] = st.session_state.audience_editor
                st.session_state.wizard_step = 4
                st.rerun()

    # Step 4: Review & Create
    elif current_step == 4:
        st.subheader("Крок 4: Перевірка та Створення")
        
        # Check if project already exists
        brand_name = st.session_state.new_project_data.get('brand_name')
        existing_projects = file_manager.list_projects()
        project_exists = brand_name in existing_projects
        
        if project_exists:
            st.warning(f"⚠️ Проект з назвою **'{brand_name}'** вже існує!")
            st.info("Оберіть, що робити:")
            
            action = st.radio(
                "Дія",
                ["Перезаписати існуючий проект", "Створити з новою назвою"],
                help="Перезапис видалить старі дані"
            )
            
            if action == "Створити з новою назвою":
                # Auto-suggest new name
                counter = 2
                new_name = f"{brand_name} ({counter})"
                while new_name in existing_projects:
                    counter += 1
                    new_name = f"{brand_name} ({counter})"
                
                new_brand_name = st.text_input(
                    "Нова назва проекту",
                    value=new_name,
                    help="Введіть унікальну назву"
                )
                st.session_state.new_project_data['brand_name'] = new_brand_name
                brand_name = new_brand_name
        
        # Show summary
        st.json(st.session_state.new_project_data)
        
        # Add save draft option
        with st.expander("💾 Зберегти чернетку (необов'язково)", expanded=False):
            st.markdown("Ви можете зберегти поточний прогрес як чернетку, щоб не втратити дані.")
            draft_name = st.text_input("Назва чернетки", value=f"{brand_name}_draft")
            if st.button("💾 Зберегти чернетку"):
                import json
                draft_path = file_manager.base_dir / f"{draft_name}.json"
                draft_path.write_text(json.dumps(st.session_state.new_project_data, indent=4, ensure_ascii=False), encoding="utf-8")
                st.success(f"Чернетку збережено: {draft_name}.json")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ Назад"):
                st.session_state.wizard_step = 3
                st.rerun()
        with c2:
            if st.button("✨ Створити Проект", type="primary"):
                try:
                    # If overwriting, delete old project first
                    if project_exists and action == "Перезаписати існуючий проект":
                        import shutil
                        old_path = file_manager.get_project_path(brand_name)
                        if old_path.exists():
                            shutil.rmtree(old_path)
                            st.info(f"Видалено старий проект '{brand_name}'")
                    
                    file_manager.create_project(st.session_state.new_project_data)
                    st.session_state['selected_project'] = brand_name
                    # Reset Wizard
                    st.session_state.wizard_step = 1
                    st.session_state.new_project_data = {}
                    st.success(f"Проект '{brand_name}' успішно створено!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Помилка створення: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    st.stop() # Stop execution until project is created/selected
else:
    # Reset wizard if user switches away from "Create New..."
    if 'wizard_step' in st.session_state:
        del st.session_state['wizard_step']
        
    if st.session_state['selected_project'] != selected_option:
        st.session_state['selected_project'] = selected_option
        st.rerun()





selected_project = st.session_state['selected_project']

# Load Project Data
tov = file_manager.read_file(selected_project, "tov.md")
assets = file_manager.get_asset_names(selected_project)

# Navigation
st.sidebar.title("Меню")
page = st.sidebar.radio("Навігація", ["📊 Дашборд", "🔍 Дослідження", "✍️ Створення", "⚙️ Налаштування"], key="main_navigation")

# Initialize session state variables if not exist
if 'research_data' not in st.session_state:
    st.session_state.research_data = None
if 'current_outline' not in st.session_state:
    st.session_state.current_outline = None
if 'generated_article' not in st.session_state:
    st.session_state.generated_article = None
if 'current_project' not in st.session_state:
    st.session_state.current_project = selected_project

# --- DASHBOARD ---
if page == "📊 Дашборд":
    st.title("📊 Панель Керування")
    st.markdown(f"### Поточний проект: **{selected_project}**")
    
    # Real Metrics
    project_path = file_manager.get_project_path(selected_project)
    total_files = len(list(project_path.glob("*.*")))
    assets_count = len(assets)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Файлів у проекті", str(total_files))
    with col2:
        st.metric("Асетів (Зображень)", str(assets_count))
    with col3:
        st.metric("Статус ToV", "✅ Заповнено" if len(tov) > 50 else "⚠️ Порожньо")

# --- RESEARCH ---
elif page == "🔍 Дослідження":
    st.title("🕵️ Аналіз Конкурентів")
    
    with st.form(key='search_form'):
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            topic = st.text_input("Введіть тему", placeholder="напр. Пресовані дріжджі")
        with col2:
            analyze_btn = st.form_submit_button("🚀 Аналізувати", use_container_width=True)
    
    if analyze_btn:
        if not API_KEY:
            st.error("⚠️ API Key не знайдено! Перевірте .env файл.")
        else:
            with st.spinner(f"Аналізую видачу для: {topic}..."):
                try:
                    serp_data = strategist.analyze_serp(topic)
                    st.session_state.research_data = serp_data
                    st.success(f"Аналіз завершено: {topic}")
                except Exception as e:
                    st.error(f"Помилка аналізу: {e}")

    if st.session_state.research_data:
        data = st.session_state.research_data
        
        # Intent & Features
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**Інтент (Намір):** {data.get('intent', 'Не визначено')}")
        with c2:
            feats = ", ".join(data.get('serp_features', []))
            st.warning(f"**SERP Фічі:** {feats if feats else 'Немає особливих фіч'}")
        
        st.subheader("🔍 Інсайти з Конкурентів")
        
        # Competitors Accordion
        if data.get('competitor_outlines'):
            for comp in data['competitor_outlines']:
                with st.expander(f"📄 {comp.get('h1', 'No Title')} ({comp['url']})"):
                    st.write("**Структура:**")
                    for h in comp.get('structure', []):
                        st.text(h)
        else:
            st.info("Детальні аутлайни конкурентів ще не завантажені. Натисніть кнопку нижче.")
            
            if st.button("📥 Завантажити структури конкурентів"):
                with st.spinner("Сканую сайти конкурентів..."):
                    urls = [r['url'] for r in data['competitors']]
                    outlines = strategist.analyze_competitors(urls)
                    st.session_state.research_data['competitor_outlines'] = outlines
                    st.rerun()

# --- WRITE ---
elif page == "✍️ Створення":
    st.title("✍️ Генератор Контенту")
    
    if not st.session_state.research_data:
        st.warning("⚠️ Спочатку проведіть дослідження у вкладці '🔍 Дослідження'!")
    else:
        st.markdown(f"### Тема: {st.session_state.research_data['topic']}")
        
        # Step 1: Outline
        if st.button("📝 Згенерувати План (Outline)"):
            with st.spinner("Створюю структуру статті..."):
                # Load ToV
                tov = file_manager.get_tov(selected_project)
                outline = writer.generate_outline(st.session_state.research_data, tov)
                st.session_state.current_outline = outline
                st.rerun()
        
        if st.session_state.current_outline:
            st.subheader("Редагування Плану")
            # Editable JSON is okay for MVP, maybe a better UI later
            edited_outline = st.data_editor(
                st.session_state.current_outline,
                num_rows="dynamic",
                use_container_width=True
            )
            
            if st.button("✅ Затвердити План і Написати Статтю", use_container_width=True):
                with st.spinner("Пишу статтю (це може зайняти хвилину)..."):
                    tov = file_manager.get_tov(selected_project)
                    keywords = ["дріжджі", "випічка", "рецепт"] # TODO: Load from semantic_core.csv
                    article = writer.write_article(edited_outline, tov, keywords)
                    st.session_state.generated_article = article
                    st.rerun()

        # Step 2: Article Review
        if st.session_state.generated_article:
            st.divider()
            st.subheader("📄 Готова Стаття")
            tab1, tab2 = st.tabs(["👁️ Попередній перегляд", "💻 HTML Код"])
            
            with tab1:
                st.markdown(st.session_state.generated_article)
            
            with tab2:
                html_content = coder.convert_to_html(st.session_state.generated_article)
                st.code(html_content, language='html')
                
                st.download_button(
                    label="💾 Завантажити HTML",
                    data=html_content,
                    file_name=f"{st.session_state.research_data['topic']}.html",
                    mime="text/html"
                )

# --- SETTINGS ---
elif page == "⚙️ Налаштування":
    st.title("⚙️ Налаштування Проекту")
    
    # Tabs for different settings
    tab1, tab2, tab3 = st.tabs(["📝 Tone of Voice", "👥 Персони", "🖼️ Асети"])
    
    with tab1:
        st.subheader("Редагування Tone of Voice")
        tov_content = st.text_area("Tone of Voice", value=tov, height=400, key="tov_settings")
        if st.button("💾 Зберегти ToV"):
            file_manager.write_file(selected_project, "tov.md", tov_content)
            st.success("ToV збережено!")
            st.rerun()
    
    with tab2:
        st.subheader("Персони вашої аудиторії")
        
        # Load config to get personas
        try:
            import json
            config_path = file_manager.get_project_path(selected_project) / "config.json"
            if config_path.exists():
                config = json.loads(config_path.read_text(encoding="utf-8"))
                audience_text = config.get("audience", "")
                
                if audience_text:
                    # Display personas in markdown
                    st.markdown(audience_text)
                    
                    # Edit option
                    with st.expander("✏️ Редагувати персони"):
                        edited_audience = st.text_area(
                            "Опис аудиторії",
                            value=audience_text,
                            height=400,
                            key="audience_settings"
                        )
                        if st.button("💾 Зберегти зміни"):
                            config["audience"] = edited_audience
                            config_path.write_text(json.dumps(config, indent=4, ensure_ascii=False), encoding="utf-8")
                            st.success("Персони оновлено!")
                            st.rerun()
                else:
                    st.info("Персони ще не створені. Створіть новий проект з персонами або додайте їх вручну.")
                    
                    # Option to generate personas for existing project
                    if st.button("✨ Згенерувати персони для цього проекту"):
                        with st.spinner("Створюю персони..."):
                            try:
                                brand_name = config.get("brand_name", selected_project)
                                industry = config.get("industry", "")
                                url = config.get("website_url", "")
                                
                                personas_text = strategist.generate_audience(
                                    brand_name,
                                    industry,
                                    url,
                                    business_model="B2C",
                                    num_personas=2
                                )
                                config["audience"] = personas_text
                                config_path.write_text(json.dumps(config, indent=4, ensure_ascii=False), encoding="utf-8")
                                st.success("Персони згенеровано!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Помилка: {e}")
            else:
                st.warning("Файл config.json не знайдено. Це старий проект без персон.")
        except Exception as e:
            st.error(f"Помилка завантаження персон: {e}")
    
    with tab3:
        st.subheader("Завантаження Асетів")
        uploaded_file = st.file_uploader("Завантажити зображення", type=["png", "jpg", "jpeg", "webp"])
        if uploaded_file:
            file_manager.save_asset(selected_project, uploaded_file.name, uploaded_file.read())
            st.success(f"Файл {uploaded_file.name} завантажено!")
            st.rerun()
        
        if assets:
            st.write("**Завантажені асети:**")
            for asset in assets:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(asset)
                with col2:
                    if st.button("🗑️", key=f"del_{asset}"):
                        file_manager.delete_asset(selected_project, asset)
                        st.rerun()
