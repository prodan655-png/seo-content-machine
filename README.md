# SEO Content Machine

AI-powered SEO content generation platform with SERP analysis, competitor research, and automated content creation.

## 🌟 Features

- 🎯 **Advanced Project Setup Wizard** with AI-powered ToV generation
- 👥 **Persona-Based Audience Analysis** with Jobs-to-be-Done framework
- 🔍 **SERP Analysis** and competitor research
- ✍️ **AI Content Generation** with outline approval
- 📊 **Real-Time Project Metrics**
- 💬 **AI Copilot** for iterative ToV refinement

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI**: Google Gemini 2.0 Flash
- **Web Scraping**: Playwright + Requests
- **Vector Database**: ChromaDB
- **Language**: Python 3.10+

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/seo-content-machine.git
cd seo-content-machine
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

5. Open your browser at `http://localhost:8501`

## 📖 Usage

### Creating a New Project

1. Click "Create New..." in the sidebar
2. Follow the 4-step wizard:
   - **Step 1**: Brand Identity (name, URL, industry)
   - **Step 2**: Tone of Voice (AI-generated with customization)
   - **Step 3**: Target Audience (persona-based with JTBD)
   - **Step 4**: Review and Create

### Generating Content

1. Go to **🔍 Дослідження** tab
2. Enter your topic
3. Analyze SERP and competitors
4. Go to **✍️ Створення** tab
5. Generate outline
6. Review and edit
7. Generate article
8. Download HTML

## 🌐 Deployment

See [Deployment Guide](streamlit_cloud_deployment.md) for detailed instructions on deploying to Streamlit Cloud.

## 📁 Project Structure

```
SEO_Machine/
├── app.py                  # Main Streamlit application
├── agents/
│   ├── strategist.py      # SERP analysis & ToV generation
│   ├── writer.py          # Content generation
│   └── coder.py           # HTML conversion
├── utils/
│   ├── file_manager.py    # Project file management
│   ├── vector_db.py       # ChromaDB integration
│   ├── sitemap_parser.py  # Sitemap parsing
│   └── seo_scorer.py      # SEO scoring
├── projects/              # User projects (gitignored)
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variables template
```

## 🔑 Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- Streamlit for the amazing framework
- Playwright for web scraping

---

Made with ❤️ by [Your Name]
