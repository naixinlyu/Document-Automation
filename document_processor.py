"""
Document processing module: extract document information using the Gemini API
"""
import json
from pathlib import Path
import google.generativeai as genai
from PIL import Image


class DocumentProcessor:
    def __init__(self, api_key: str):
        """Initialize with the API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    def _load_image(self, file_path: str) -> Image.Image:
        """Load an image or convert the first page of a PDF to an image"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == ".pdf":
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(file_path, first_page=1, last_page=1, dpi=200)
                if images:
                    return images[0]
            except Exception as e:
                raise ValueError(f"PDF conversion failed: {e}")
        else:
            return Image.open(file_path)
        
        raise ValueError(f"Unsupported file type: {suffix}")
    
    def _parse_json_response(self, text: str) -> dict:
        """Parse JSON from the model response text"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse response", "raw_response": text[:500]}
    
    async def extract_passport_info(self, file_path: str) -> dict:
        """Extract information from a passport"""
        try:
            image = self._load_image(file_path)
        except Exception as e:
            return {"error": f"File processing failed: {str(e)}"}
        
        prompt = """Please analyze this passport image and extract the following information.
Return the data in a structured JSON format.

Extract these fields:
- full_name: Full name as shown on passport
- first_name: First/Given name
- last_name: Last/Family/Surname  
- date_of_birth: Date of birth (format: YYYY-MM-DD)
- passport_number: Passport number
- nationality: Country/Nationality
- gender: Gender (Male/Female)
- place_of_birth: Place of birth
- date_of_issue: Issue date (format: YYYY-MM-DD)
- date_of_expiry: Expiry date (format: YYYY-MM-DD)
- issuing_country: Country that issued the passport

If any field cannot be found or is unclear, use "N/A".

IMPORTANT: Respond ONLY with a valid JSON object, no other text. Example:
{
    "full_name": "JOHN DOE",
    "first_name": "JOHN",
    "last_name": "DOE",
    "date_of_birth": "1990-01-15",
    "passport_number": "AB1234567",
    "nationality": "United States",
    "gender": "Male",
    "place_of_birth": "New York",
    "date_of_issue": "2020-01-01",
    "date_of_expiry": "2030-01-01",
    "issuing_country": "United States"
}"""
        
        try:
            response = self.model.generate_content([prompt, image])
            return self._parse_json_response(response.text)
        except Exception as e:
            return {"error": f"API call failed: {str(e)}"}
    
    async def extract_g28_info(self, file_path: str) -> dict:
        """Extract information from a G-28 form"""
        try:
            image = self._load_image(file_path)
        except Exception as e:
            return {"error": f"File processing failed: {str(e)}"}
        
        prompt = """Please analyze this G-28 form and extract the following information.

Extract these fields:
- attorney_name: Attorney or representative's full name
- attorney_first_name: Attorney's first name
- attorney_last_name: Attorney's last name
- firm_name: Law firm or organization name
- attorney_address: Full street address
- attorney_city: City
- attorney_state: State
- attorney_zip: ZIP or postal code
- attorney_phone: Phone number
- attorney_fax: Fax number
- attorney_email: Email address
- bar_number: Bar number or license number
- uscis_online_account: USCIS online account number
- client_name: Name of the client
- client_alien_number: Alien registration number (A-Number)
- daytime_phone: Daytime phone number

If any field cannot be found, use "N/A".

IMPORTANT: Respond ONLY with a valid JSON object, no other text. Example:
{
    "attorney_name": "Jane Smith",
    "attorney_first_name": "Jane",
    "attorney_last_name": "Smith",
    "firm_name": "Smith Law Firm",
    "attorney_address": "123 Legal Street",
    "attorney_city": "Los Angeles",
    "attorney_state": "CA",
    "attorney_zip": "90001",
    "attorney_phone": "555-123-4567",
    "attorney_fax": "N/A",
    "attorney_email": "jane@smithlaw.com",
    "bar_number": "123456",
    "uscis_online_account": "N/A",
    "client_name": "John Doe",
    "client_alien_number": "A123456789",
    "daytime_phone": "555-987-6543"
}"""
        
        try:
            response = self.model.generate_content([prompt, image])
            return self._parse_json_response(response.text)
        except Exception as e:
            return {"error": f"API call failed: {str(e)}"}
