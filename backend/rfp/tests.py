import unittest
from unittest.mock import patch, MagicMock
import json
from rfp.utils import extract_rfp_from_text


class TestExtractRFPFromText(unittest.TestCase):
    """Test cases for extract_rfp_from_text function."""
    
    def test_empty_input_raises_error(self):
        """Test that empty input raises ValueError."""
        with self.assertRaises(ValueError):
            extract_rfp_from_text("")
        
        with self.assertRaises(ValueError):
            extract_rfp_from_text("   ")
    
    @patch.dict('os.environ', {}, clear=True)
    def test_missing_api_key(self):
        """Test handling when GEMINI_API_KEY is not set."""
        result = extract_rfp_from_text("Test input")
        
        self.assertFalse(result['success'])
        self.assertIn('GEMINI_API_KEY', result['error'])
        self.assertIsNone(result['title'])
        self.assertIsNone(result['budget'])
        self.assertIsNone(result['deadline'])
        self.assertEqual(result['items'], [])
    
    @patch('rfp.utils.genai.GenerativeModel')
    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'})
    def test_successful_extraction(self, mock_model):
        """Test successful extraction of RFP data."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            'title': 'Office Laptop Purchase',
            'budget': 75000,
            'deadline': '2024-03-15',
            'items': [
                {
                    'name': 'Laptops',
                    'quantity': 50,
                    'specifications': '16GB RAM, 512GB SSD, Intel i7'
                },
                {
                    'name': 'External Monitors',
                    'quantity': 10,
                    'specifications': '27 inch, 4K resolution'
                }
            ]
        })
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        # Test
        result = extract_rfp_from_text("Need 50 laptops and 10 monitors, budget $75k")
        
        self.assertTrue(result['success'])
        self.assertIsNone(result['error'])
        self.assertEqual(result['title'], 'Office Laptop Purchase')
        self.assertEqual(result['budget'], 75000.0)
        self.assertEqual(result['deadline'], '2024-03-15')
        self.assertEqual(len(result['items']), 2)
        self.assertEqual(result['items'][0]['name'], 'Laptops')
        self.assertEqual(result['items'][0]['quantity'], 50)
    
    @patch('rfp.utils.genai.GenerativeModel')
    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'})
    def test_json_parsing_error(self, mock_model):
        """Test handling of invalid JSON response."""
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = extract_rfp_from_text("Test input")
        
        self.assertFalse(result['success'])
        self.assertIn('Failed to parse JSON', result['error'])
    
    @patch('rfp.utils.genai.GenerativeModel')
    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'})
    def test_api_exception_handling(self, mock_model):
        """Test handling of API exceptions."""
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_instance
        
        result = extract_rfp_from_text("Test input")
        
        self.assertFalse(result['success'])
        self.assertIn('Exception', result['error'])
        self.assertIn('API Error', result['error'])
    
    @patch('rfp.utils.genai.GenerativeModel')
    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'})
    def test_markdown_json_cleanup(self, mock_model):
        """Test cleaning of markdown-formatted JSON response."""
        mock_response = MagicMock()
        mock_response.text = '''```json
{
    "title": "Test RFP",
    "budget": 10000,
    "deadline": null,
    "items": []
}
```'''
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_instance
        
        result = extract_rfp_from_text("Test input")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['title'], 'Test RFP')
        self.assertEqual(result['budget'], 10000.0)


if __name__ == '__main__':
    unittest.main()
