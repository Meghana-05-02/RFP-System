import json
import os
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
# Try multiple locations: current dir, parent dir, and rfp app dir
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def extract_rfp_from_text(natural_language_input: str) -> Dict[str, Any]:
    """
    Extract structured RFP data from natural language text using Gemini API.
    
    Args:
        natural_language_input: Natural language description of RFP requirements
        
    Returns:
        Dictionary containing:
            - title: str
            - budget: float or None
            - deadline: str (ISO format) or None
            - items: List[Dict] with keys: name, quantity, specifications
            - success: bool
            - error: str or None
            
    Raises:
        ValueError: If natural_language_input is empty or invalid
    """
    if not natural_language_input or not natural_language_input.strip():
        raise ValueError("Natural language input cannot be empty")
    
    # Get API key from environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return {
            'success': False,
            'error': 'GEMINI_API_KEY environment variable not set',
            'title': None,
            'budget': None,
            'deadline': None,
            'items': []
        }
    
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash - stable version
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create prompt for structured extraction
        prompt = f"""
You are an RFP (Request for Proposal) data extraction assistant. 
Analyze the following natural language RFP description and extract structured data.

RFP Description:
{natural_language_input}

Extract and return a JSON object with the following structure:
{{
    "title": "Brief descriptive title for the RFP",
    "budget": <numeric value or null if not mentioned>,
    "deadline": "YYYY-MM-DD format or null if not mentioned",
    "items": [
        {{
            "name": "Item name",
            "quantity": <numeric value, default to 1 if not specified>,
            "specifications": "Technical specifications or requirements"
        }}
    ]
}}

Rules:
1. Extract budget as a numeric value without currency symbols
2. Convert any date mentions to YYYY-MM-DD format
3. If multiple items are mentioned, create separate entries in the items array
4. If no specific items are mentioned, infer from the context
5. Return ONLY valid JSON, no additional text or markdown formatting

JSON:
"""
        
        # Make API call with timeout and safety settings
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.1,  # Low temperature for more consistent extraction
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
        
        # Extract and parse response
        if not response or not response.text:
            return {
                'success': False,
                'error': 'Empty response from Gemini API',
                'title': None,
                'budget': None,
                'deadline': None,
                'items': []
            }
        
        # Clean response text (remove markdown code blocks if present)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Failed to parse JSON response: {str(e)}',
                'title': None,
                'budget': None,
                'deadline': None,
                'items': [],
                'raw_response': response_text
            }
        
        # Validate and normalize extracted data
        result = {
            'success': True,
            'error': None,
            'title': extracted_data.get('title', 'Untitled RFP'),
            'budget': extracted_data.get('budget'),
            'deadline': extracted_data.get('deadline'),
            'items': extracted_data.get('items', [])
        }
        
        # Validate budget is numeric or None
        if result['budget'] is not None:
            try:
                result['budget'] = float(result['budget'])
            except (ValueError, TypeError):
                result['budget'] = None
        
        # Validate deadline format
        if result['deadline']:
            try:
                datetime.fromisoformat(result['deadline'])
            except (ValueError, TypeError):
                result['deadline'] = None
        
        # Validate items structure
        validated_items = []
        for item in result['items']:
            if isinstance(item, dict) and 'name' in item:
                validated_item = {
                    'name': str(item.get('name', '')),
                    'quantity': int(item.get('quantity', 1)),
                    'specifications': str(item.get('specifications', ''))
                }
                validated_items.append(validated_item)
        result['items'] = validated_items
        
        return result
        
    except Exception as e:
        # Handle any unexpected errors
        error_type = type(e).__name__
        error_message = str(e)
        
        return {
            'success': False,
            'error': f'{error_type}: {error_message}',
            'title': None,
            'budget': None,
            'deadline': None,
            'items': []
        }


def extract_proposal_from_email(email_body: str) -> Dict[str, Any]:
    """
    Extract structured proposal data from email body using Gemini API.
    
    Args:
        email_body: Email body text containing proposal information
        
    Returns:
        Dictionary containing:
            - price: float or None
            - payment_terms: str or None
            - warranty: str or None
            - success: bool
            - error: str or None
            
    Raises:
        ValueError: If email_body is empty or invalid
    """
    if not email_body or not email_body.strip():
        raise ValueError("Email body cannot be empty")
    
    # Get API key from environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return {
            'success': False,
            'error': 'GEMINI_API_KEY environment variable not set',
            'price': None,
            'payment_terms': None,
            'warranty': None
        }
    
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Create prompt for proposal extraction
        prompt = f"""
You are a proposal data extraction assistant. 
Analyze the following email body which contains a vendor's proposal/quote response.

Email Body:
{email_body}

Extract and return a JSON object with the following structure:
{{
    "price": <total price as numeric value or null if not found>,
    "payment_terms": "Payment terms description or null",
    "warranty": "Warranty information or null"
}}

Rules:
1. Extract the total price/quote amount as a numeric value without currency symbols
2. Extract payment terms (e.g., "Net 30", "50% upfront, 50% on delivery", etc.)
3. Extract warranty information (e.g., "1 year warranty", "90 days limited warranty", etc.)
4. If any field is not mentioned in the email, set it to null
5. Return ONLY valid JSON, no additional text or markdown formatting

JSON:
"""
        
        # Make API call
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.1,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 1024,
            },
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
        
        # Extract and parse response
        if not response or not response.text:
            return {
                'success': False,
                'error': 'Empty response from Gemini API',
                'price': None,
                'payment_terms': None,
                'warranty': None
            }
        
        # Clean response text
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Failed to parse JSON response: {str(e)}',
                'price': None,
                'payment_terms': None,
                'warranty': None,
                'raw_response': response_text
            }
        
        # Validate and normalize extracted data
        result = {
            'success': True,
            'error': None,
            'price': extracted_data.get('price'),
            'payment_terms': extracted_data.get('payment_terms'),
            'warranty': extracted_data.get('warranty')
        }
        
        # Validate price is numeric or None
        if result['price'] is not None:
            try:
                result['price'] = float(result['price'])
            except (ValueError, TypeError):
                result['price'] = None
        
        return result
        
    except Exception as e:
        # Handle any unexpected errors
        error_type = type(e).__name__
        error_message = str(e)
        
        return {
            'success': False,
            'error': f'{error_type}: {error_message}',
            'price': None,
            'payment_terms': None,
            'warranty': None
        }


# Example usage and testing
if __name__ == '__main__':
    # Test RFP extraction
    test_rfp_input = """
    We need to purchase 50 laptops for our office with the following specs:
    - 16GB RAM
    - 512GB SSD
    - Intel i7 processor
    
    We also need 10 external monitors (27 inch, 4K resolution).
    Our budget is $75,000 and we need delivery by March 15, 2024.
    """
    
    result = extract_rfp_from_text(test_rfp_input)
    print("RFP Extraction:")
    print(json.dumps(result, indent=2))
    
    # Test proposal extraction
    test_proposal_input = """
    Dear Customer,
    
    Thank you for your RFP request. We are pleased to submit our proposal:
    
    Total Quote: $68,500
    
    Payment Terms: 30% upfront, 70% upon delivery
    
    Warranty: All items come with 2-year manufacturer warranty and 90-day satisfaction guarantee.
    
    Best regards,
    Vendor ABC
    """
    
    proposal_result = extract_proposal_from_email(test_proposal_input)
    print("\nProposal Extraction:")
    print(json.dumps(proposal_result, indent=2))
