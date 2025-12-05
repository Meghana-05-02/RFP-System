import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / 'rfp' / '.env'
load_dotenv(dotenv_path=env_path)

print("Environment Check:")
print(f"1. .env file path: {env_path}")
print(f"2. .env file exists: {env_path.exists()}")

api_key = os.getenv('GEMINI_API_KEY')
print(f"3. API key loaded: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"4. API key length: {len(api_key)} characters")
    print(f"5. API key starts with: {api_key[:10]}...")

print("\nNow testing the extraction function...")
from rfp.utils import extract_rfp_from_text
import json

result = extract_rfp_from_text('We need 10 laptops. Budget is 50000 dollars.')
print(json.dumps(result, indent=2))
