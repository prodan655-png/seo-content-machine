import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from utils.vector_db import VectorDB
from agents.coder import Coder

class TestSitemapIntegration(unittest.TestCase):
    
    def setUp(self):
        # Mock VectorDB
        self.mock_vector_db = MagicMock()
        self.coder = Coder(self.mock_vector_db)

    def test_internal_linking(self):
        """Test if Coder correctly injects links based on VectorDB data."""
        
        # Mock data from VectorDB
        self.mock_vector_db.get_all_pages.return_value = [
            {"url": "https://example.com/whisky", "title": "Whisky Guide"},
            {"url": "https://example.com/yeast", "title": "Best Yeast"}
        ]
        
        html_input = """
        <html>
            <body>
                <p>Read our comprehensive Whisky Guide to learn more.</p>
                <p>We also sell the Best Yeast for baking.</p>
                <p>This text has no matches.</p>
            </body>
        </html>
        """
        
        expected_output_snippet_1 = '<a href="https://example.com/whisky" title="Whisky Guide">Whisky Guide</a>'
        expected_output_snippet_2 = '<a href="https://example.com/yeast" title="Best Yeast">Best Yeast</a>'
        
        result = self.coder.inject_internal_links(html_input, "TestBrand")
        
        print(f"Input: {html_input}")
        print(f"Result: {result}")
        
        self.assertIn(expected_output_snippet_1, result)
        self.assertIn(expected_output_snippet_2, result)
        
    def test_internal_linking_no_duplicates(self):
        """Test that it doesn't link the same URL twice."""
        self.mock_vector_db.get_all_pages.return_value = [
            {"url": "https://example.com/whisky", "title": "Whisky"}
        ]
        
        html_input = "<p>Whisky is great. I love Whisky.</p>"
        
        result = self.coder.inject_internal_links(html_input, "TestBrand")
        
        # Should only have one link
        self.assertEqual(result.count('<a href="https://example.com/whisky"'), 1)

if __name__ == '__main__':
    unittest.main()
