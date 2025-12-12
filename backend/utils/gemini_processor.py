"""
Gemini AI Processor for register data extraction
File: backend/utils/gemini_processor.py
"""
import os
import re
import json
import time
import google.generativeai as genai
from typing import Dict, Any


class GeminiProcessor:
    """Process documents with Gemini AI to extract structured register data"""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini processor with API key"""
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY environment variable.")
        
        genai.configure(api_key=api_key)
        
        # Use models that actually exist in your API (from debug output)
        # Priority: Stable > Latest > Experimental
        model_names_to_try = [
            'models/gemini-2.5-flash',        # Newest stable flash (June 2025)
            'models/gemini-flash-latest',     # Always points to latest flash
            'models/gemini-2.0-flash',        # Previous stable flash
            'models/gemini-2.0-flash-001',    # Stable 2.0 flash (Jan 2025)
            'models/gemini-pro-latest',       # Latest pro model
            'models/gemini-2.5-pro',          # Stable pro model
        ]
        
        self.model = None
        last_error = None
        
        # Try to initialize with available models
        for model_name in model_names_to_try:
            try:
                print(f"Trying to initialize model: {model_name}")
                self.model = genai.GenerativeModel(model_name)
                print(f"✓ Successfully initialized model: {model_name}")
                break
            except Exception as e:
                last_error = str(e)
                print(f"⚠ Failed to initialize {model_name}: {e}")
                continue
        
        if not self.model:
            # List available models for debugging
            try:
                print("\n📋 Listing available models:")
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        print(f"  - {m.name}")
            except Exception as e:
                print(f"Could not list models: {e}")
            
            raise ValueError(f"Could not initialize any Gemini model. Last error: {last_error}")
        
        self.max_retries = 3
        self.temperature = 0.1
        self.top_p = 0.95
        self.max_output_tokens = 8192
        
        # Safety settings
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    
    def process_document(self, raw_data: str, device_name: str) -> Dict[str, Any]:
        """Process document with AI to extract register data"""
        print("Processing document with AI extraction...")
        
        # Preprocess data
        cleaned_data = self._preprocess_data(raw_data)
        
        # Limit data to avoid token limits
        # Gemini 2.5 Flash has 1M token context, but we'll use 10k chars to be safe
        cleaned_data = cleaned_data[:10000]
        
        # Save input for debugging
        try:
            with open('gemini_input.txt', 'w', encoding='utf-8') as f:
                f.write(cleaned_data)
            print(f"Saved Gemini input to gemini_input.txt ({len(cleaned_data)} chars)")
        except Exception as e:
            print(f"Warning: Could not save debug file: {e}")
        
        # Create extraction prompt
        prompt = self._create_extraction_prompt(cleaned_data, device_name)
        
        # Try extraction with retries and exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                print(f"Sending request to Gemini (attempt {attempt + 1}/{self.max_retries})...")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        top_p=self.top_p,
                        max_output_tokens=self.max_output_tokens,
                    ),
                    safety_settings=self.safety_settings
                )
                
                print("✓ Received response from Gemini")
                
                if hasattr(response, 'text') and response.text:
                    # Save response for debugging
                    try:
                        with open(f'gemini_response_attempt_{attempt + 1}.txt', 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print(f"Saved raw response to gemini_response_attempt_{attempt + 1}.txt")
                    except Exception as e:
                        print(f"Warning: Could not save response file: {e}")
                    
                    # Extract and parse JSON
                    text = response.text.strip()
                    json_str = self._extract_json(text)
                    register_data = json.loads(json_str)
                    
                    # Validate and normalize structure
                    register_data = self._validate_structure(register_data, device_name)
                    
                    num_registers = len(register_data.get('registers', []))
                    total_fields = sum(len(reg.get('fields', [])) for reg in register_data['registers'])
                    print(f"✓ Extracted {num_registers} register(s) with {total_fields} total fields")
                    
                    return register_data
                else:
                    raise ValueError("No valid text in Gemini response")
                    
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                print(f"⚠ Error on attempt {attempt + 1}: {error_msg}")
                
                # Check if it's a quota/rate limit error
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    print("⚠ Rate limit/quota exceeded. Please wait or check your API key.")
                    if attempt < self.max_retries - 1:
                        wait_time = 5 * (2 ** attempt)  # 5s, 10s, 20s
                        print(f"⏳ Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise ValueError(f"Rate limit exceeded. Please:\n1. Wait a few minutes\n2. Check your API usage at https://ai.google.dev/usage\n3. Upgrade your API plan if needed")
                
                # For other errors, use shorter backoff
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                    
        raise ValueError(f"Failed to extract register data after {self.max_retries} attempts: {last_error}")
    
    def _create_extraction_prompt(self, data: str, device_name: str) -> str:
        """Create extraction prompt for Gemini"""
        return f"""You are a hardware register specification extraction expert. Extract ONLY the CTRL (Control) register information from the provided document and return ONLY valid JSON (no markdown, no code fences, no explanations).

DOCUMENT DATA:
{data}

EXTRACTION RULES:
1. Extract ONLY the CTRL (Control) register - ignore all other registers
2. Preserve exact register name, field names, and ID from the document
3. Detect register width from the document (16-bit or 32-bit)
4. Extract all bit fields with their exact positions, widths, and access modes
5. Include reserved/unused bit ranges
6. Extract all field value enumerations with descriptions
7. Preserve offset address exactly as specified (convert formats like "4h" to "0x4")
8. Extract complete register description

JSON STRUCTURE:
{{
  "device_name": "{device_name}",
  "registers": [
    {{
      "name": "<full CTRL register name from doc>",
      "id": "CTRL",
      "brief_desc": "<short description>",
      "long_desc": "<detailed description>",
      "offset": "<address in 0xNN format>",
      "width": <16 or 32>,
      "reset_value": "<default value in 0xNN format>",
      "fields": [
        {{
          "name": "<field name from doc>",
          "id": "<field ID>",
          "position": <LSB position>,
          "width": <number of bits>,
          "access": "<RW|RO|WO|ROZ>",
          "brief_desc": "<short description>",
          "long_desc": "<detailed description>",
          "reserved": <true if reserved, false otherwise>,
          "modified_write": "<oneToClear|oneToSet|etc or omit>",
          "values": [
            {{
              "id": "<VALUE_ID>",
              "value": "<0b0|0b1|etc>",
              "desc": "<description>",
              "usage": "<read|write|readWrite or omit>"
            }}
          ]
        }}
      ]
    }}
  ]
}}

CRITICAL: Return ONLY the JSON object with the CTRL register. No explanations, no markdown formatting."""
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from response text"""
        # Remove markdown code blocks
        text = re.sub(r'```[\w]*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Find JSON boundaries
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start < 0 or end <= start:
            raise ValueError("No valid JSON found in response")
        
        return text[start:end]
    
    def _preprocess_data(self, raw_data: str) -> str:
        """Preprocess raw data for better extraction"""
        if isinstance(raw_data, list):
            raw_data = '\n\n'.join(str(item) for item in raw_data)
        
        # Clean up whitespace
        raw_data = re.sub(r'[ \t]+', ' ', raw_data)
        raw_data = re.sub(r'\s+\n', '\n', raw_data)
        raw_data = raw_data.replace('NO TE', 'NOTE').strip()
        
        # Remove non-ASCII characters
        raw_data = re.sub(r'[^\x00-\x7F]+', ' ', raw_data)
        
        return raw_data
    
    def _validate_structure(self, data: Dict[str, Any], device_name: str) -> Dict[str, Any]:
        """Validate and normalize JSON structure"""
        if not data.get('registers'):
            raise ValueError("No registers found in extracted data")
        
        data['device_name'] = device_name
        
        for reg in data['registers']:
            # Set defaults for register
            reg.setdefault('name', 'UNKNOWN')
            reg.setdefault('id', reg['name'])
            reg.setdefault('width', 32)
            reg.setdefault('reset_value', '0x0')
            reg.setdefault('brief_desc', '')
            reg.setdefault('long_desc', '')
            reg.setdefault('fields', [])
            
            # Normalize offset format
            if 'offset' in reg:
                offset = reg['offset']
                if isinstance(offset, str):
                    offset = offset.strip().upper()
                    offset = re.sub(r'H$', '', offset)
                    if not offset.startswith('0X'):
                        try:
                            int(offset, 16)
                            offset = f'0x{offset}'
                        except:
                            offset = '0x0'
                    reg['offset'] = offset.lower()
                else:
                    reg['offset'] = f'0x{offset:X}'.lower()
            else:
                reg['offset'] = '0x0'
            
            # Validate fields
            for field in reg['fields']:
                field.setdefault('name', 'UNKNOWN')
                field.setdefault('id', field['name'])
                field.setdefault('reserved', False)
                field.setdefault('values', [])
                field.setdefault('access', 'RW')
                field.setdefault('brief_desc', '')
                field.setdefault('long_desc', '')
                field.setdefault('position', 0)
                field.setdefault('width', 1)
                
                # Validate field values
                for value in field.get('values', []):
                    value.setdefault('id', 'UNKNOWN')
                    value.setdefault('value', '0b0')
                    value.setdefault('desc', '')
        
        return data