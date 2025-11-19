import os
from dotenv import load_dotenv
from agents.strategist import Strategist

# Load environment
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env file!")
    exit(1)

print(f"API Key found: {API_KEY[:10]}...")

# Initialize strategist
strategist = Strategist(API_KEY)

# Test ToV generation
print("\n=== Testing ToV Generation ===")
brand_name = "Світ Пекаря"
industry = "E-commerce"
url = "https://svitpekaria.com.ua/"

print(f"Brand: {brand_name}")
print(f"Industry: {industry}")
print(f"URL: {url}")
print("\nGenerating ToV...")

try:
    tov = strategist.generate_tov(brand_name, industry, url)
    print(f"\n=== SUCCESS ===")
    print(f"Generated ToV (length: {len(tov)} characters):")
    print("=" * 50)
    print(tov)
    print("=" * 50)
except Exception as e:
    print(f"\n=== ERROR ===")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
