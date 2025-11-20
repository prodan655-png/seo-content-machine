import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from utils.report_generator import generate_brand_book_html
except ImportError:
    # If running from root, utils might not be in path directly if not a package
    sys.path.append(os.path.join(os.getcwd(), 'utils'))
    from utils.report_generator import generate_brand_book_html

# Mock Data
brand_name = "Test Brand"
tov_text = "# Tone of Voice\n\nFriendly and professional."
personas_text = "# Personas\n\n## Persona 1\n\nManager."
cjm_text = "# CJM\n\n| Stage | Action |\n| --- | --- |\n| Awareness | Ads |"

# Generate HTML
try:
    html = generate_brand_book_html(brand_name, tov_text, personas_text, cjm_text)
    print(f"Successfully generated HTML. Length: {len(html)}")
    
    # Save for inspection
    with open("test_brand_book.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved to test_brand_book.html")
    
except Exception as e:
    print(f"Error: {e}")
