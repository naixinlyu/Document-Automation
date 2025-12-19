"""
Form filling module: automatically fill web forms using Selenium
"""
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class FormFiller:
    def __init__(self):
        self.form_url = "https://mendrika-alma.github.io/form-submission/"
    
    async def fill_form(self, passport_data: dict, g28_data: dict) -> dict:
        """Fill the form using the extracted data."""
        
        # Set Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1280,900")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--headless=new")  # Use headless mode
        chrome_options.add_argument("--disable-logging")  # Disable logging
        chrome_options.add_argument("--log-level=3")  # Only show fatal errors
        chrome_options.add_argument("--disable-gcm")  # Disable Google Cloud Messaging
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress logging
        
        driver = None
        try:
            # Auto-download and manage ChromeDriver
            # On Windows, ensure we get the correct executable
            driver_path = ChromeDriverManager().install()
            # Suppress ChromeDriver logging by redirecting to null
            import os
            service = Service(driver_path, service_log_path=os.devnull)
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            # Fallback: try without explicit service (uses system PATH)
            print(f"Warning: ChromeDriverManager failed ({e}), trying system ChromeDriver...")
            try:
                driver = webdriver.Chrome(options=chrome_options)
            except Exception as e2:
                raise Exception(f"Failed to initialize ChromeDriver: {e2}. Please ensure Chrome browser is installed and ChromeDriver is available.")
        
        filled_fields = []
        errors = []
        
        if driver is None:
            raise Exception("Failed to initialize ChromeDriver")
        
        try:
            # Navigate to the form page
            print(f"Visiting form: {self.form_url}")
            driver.get(self.form_url)
            time.sleep(2)  
            
            print("Starting to fill the form...")
            
            # Analyze form structure
            self._analyze_form_structure(driver)
            
            # Helper function to format date from YYYY-MM-DD to mm/dd/yyyy
            def format_date(date_str):
                if not date_str or date_str == "N/A":
                    return None
                try:
                    from datetime import datetime
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    return dt.strftime("%m/%d/%Y")
                except:
                    return date_str
            
            # Helper function to format gender
            def format_gender(gender_str):
                if not gender_str or gender_str == "N/A":
                    return None
                gender_lower = gender_str.lower()
                if "female" in gender_lower or gender_lower == "f":
                    return "F"
                elif "male" in gender_lower or gender_lower == "m":
                    return "M"
                return gender_str
            
            # Helper function to format state (convert abbreviation to full name)
            def format_state(state_str):
                if not state_str or state_str == "N/A":
                    return None
                state_abbrev_map = {
                    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
                    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
                    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
                    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
                    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
                    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
                    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
                    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
                    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
                    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
                    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
                    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
                    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
                }
                state_upper = state_str.upper().strip()
                return state_abbrev_map.get(state_upper, state_str)
            
            # Helper function to fill a field by ID
            def fill_field_by_id(field_id, value, field_name=""):
                if not value or value == "N/A" or value == "":
                    return False
                try:
                    element = driver.find_element(By.ID, field_id)
                    if element.is_displayed():
                        tag_name = element.tag_name.lower()
                        input_type = element.get_attribute("type") or ""
                        
                        if tag_name == "select":
                            select = Select(element)
                            try:
                                select.select_by_visible_text(str(value))
                            except:
                                try:
                                    select.select_by_value(str(value))
                                except:
                                    # Try partial match
                                    for option in select.options:
                                        if str(value).lower() in option.text.lower() or option.text.lower() in str(value).lower():
                                            select.select_by_visible_text(option.text)
                                            break
                        elif input_type == "date":
                            # For date fields, format the value
                            formatted_value = format_date(value) if isinstance(value, str) and "-" in value else value
                            element.clear()
                            element.send_keys(str(formatted_value))
                        else:
                            element.clear()
                            element.send_keys(str(value))
                        
                        display_name = field_name if field_name else field_id
                        filled_fields.append(display_name)
                        print(f"  {display_name}: {value}")
                        return True
                except Exception as e:
                    return False
                return False
            
            # PART 1: Information About Attorney or Representative (from G-28 data)
            print("\nFilling Part 1: Attorney Information...")
            
            # Attorney name fields (from G-28)
            if "attorney_last_name" in g28_data or "attorney_name" in g28_data:
                attorney_last = g28_data.get("attorney_last_name") or (g28_data.get("attorney_name", "").split()[-1] if g28_data.get("attorney_name") else "")
                fill_field_by_id("family-name", attorney_last, "attorney_family_name")
            
            if "attorney_first_name" in g28_data or "attorney_name" in g28_data:
                attorney_first = g28_data.get("attorney_first_name") or (g28_data.get("attorney_name", "").split()[0] if g28_data.get("attorney_name") else "")
                fill_field_by_id("given-name", attorney_first, "attorney_given_name")
            
            # Attorney address (from G-28)
            fill_field_by_id("street-number", g28_data.get("attorney_address"), "attorney_address")
            fill_field_by_id("city", g28_data.get("attorney_city"), "attorney_city")
            state_formatted = format_state(g28_data.get("attorney_state"))
            fill_field_by_id("state", state_formatted, "attorney_state")
            fill_field_by_id("zip", g28_data.get("attorney_zip"), "attorney_zip")
            # Note: country field in Part 1 should probably be left empty or set to "United States"
            
            # Attorney contact (from G-28)
            fill_field_by_id("daytime-phone", g28_data.get("attorney_phone") or g28_data.get("daytime_phone"), "attorney_phone")
            fill_field_by_id("email", g28_data.get("attorney_email"), "attorney_email")
            
            # PART 2: Eligibility Information (from G-28 data)
            print("\nFilling Part 2: Eligibility Information...")
            fill_field_by_id("bar-number", g28_data.get("bar_number"), "bar_number")
            fill_field_by_id("law-firm", g28_data.get("firm_name"), "firm_name")
            
            # PART 3: Passport Information for the Beneficiary (from Passport data)
            print("\nFilling Part 3: Passport Information...")
            fill_field_by_id("passport-surname", passport_data.get("last_name"), "passport_last_name")
            fill_field_by_id("passport-given-names", passport_data.get("first_name"), "passport_first_name")
            fill_field_by_id("passport-number", passport_data.get("passport_number"), "passport_number")
            fill_field_by_id("passport-country", passport_data.get("issuing_country"), "passport_country")
            fill_field_by_id("passport-nationality", passport_data.get("nationality"), "passport_nationality")
            
            # Date of birth - format it
            dob_formatted = format_date(passport_data.get("date_of_birth"))
            fill_field_by_id("passport-dob", dob_formatted, "passport_dob")
            
            fill_field_by_id("passport-pob", passport_data.get("place_of_birth"), "passport_place_of_birth")
            
            # Gender/Sex - format it
            gender_formatted = format_gender(passport_data.get("gender"))
            fill_field_by_id("passport-sex", gender_formatted, "passport_sex")
            
            # Issue and expiry dates - format them
            issue_date_formatted = format_date(passport_data.get("date_of_issue"))
            fill_field_by_id("passport-issue-date", issue_date_formatted, "passport_issue_date")
            
            expiry_date_formatted = format_date(passport_data.get("date_of_expiry"))
            fill_field_by_id("passport-expiry-date", expiry_date_formatted, "passport_expiry_date")
            
            print(f"\nFilling completed. Total fields filled: {len(filled_fields)}")
            
            print("Waiting 5 seconds for review...")
            time.sleep(5)
            
            # Full page screenshot
            screenshot_path = "uploads/form_filled.png"
            self._take_full_page_screenshot(driver, screenshot_path)
            print(f"Full page screenshot saved: {screenshot_path}")
            
            return {
                "filled_fields": filled_fields,
                "errors": errors,
                "screenshot": "form_filled.png",
                "total_filled": len(filled_fields)
            }
            
        except Exception as e:
            errors.append(str(e))
            print(f"Error: {e}")
            return {
                "filled_fields": filled_fields,
                "errors": errors,
                "screenshot": None,
                "total_filled": len(filled_fields)
            }
        finally:
            if driver is not None:
                try:
                    time.sleep(3)
                    driver.quit()
                except Exception as e:
                    print(f"Error closing driver: {e}")
    
    def _analyze_form_structure(self, driver):
        """Analyze form structure"""
        print("\nAnalyzing form structure...")
        
        inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
        
        for inp in inputs:
            try:
                if inp.is_displayed():
                    tag = inp.tag_name
                    name = inp.get_attribute("name") or ""
                    id_attr = inp.get_attribute("id") or ""
                    placeholder = inp.get_attribute("placeholder") or ""
                    input_type = inp.get_attribute("type") or ""
                    
                    if name or id_attr:
                        print(f"  - {tag}[name='{name}', id='{id_attr}', type='{input_type}', placeholder='{placeholder}']")
            except:
                continue
        
        print("")
    
    def _fill_by_label_or_placeholder(self, driver, data_key: str, value: str) -> bool:
        """Find and fill by label or placeholder"""
        
        label_texts = {
            "first_name": ["First Name", "Given Name", "First"],
            "last_name": ["Last Name", "Family Name", "Surname", "Last"],
            "full_name": ["Full Name", "Name", "Complete Name"],
            "date_of_birth": ["Date of Birth", "DOB", "Birth Date", "Birthday"],
            "passport_number": ["Passport Number", "Passport No", "Passport"],
            "nationality": ["Nationality", "Country", "Citizenship"],
            "gender": ["Gender", "Sex"],
            "place_of_birth": ["Place of Birth", "Birthplace"],
            "attorney_name": ["Attorney Name", "Representative Name", "Lawyer"],
            "firm_name": ["Law Firm", "Firm Name", "Organization", "Company"],
            "attorney_address": ["Address", "Street Address"],
            "attorney_city": ["City"],
            "attorney_state": ["State", "Province"],
            "attorney_zip": ["ZIP", "ZIP Code", "Postal Code"],
            "attorney_phone": ["Phone", "Phone Number", "Telephone"],
            "attorney_email": ["Email", "Email Address"],
            "bar_number": ["Bar Number", "License Number"],
        }
        
        texts_to_try = label_texts.get(data_key, [])
        
        for label_text in texts_to_try:
            try:
                # Try locating by placeholder
                inputs = driver.find_elements(By.CSS_SELECTOR, 
                    f'input[placeholder*="{label_text}" i], textarea[placeholder*="{label_text}" i]')
                
                for inp in inputs:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(str(value))
                        return True
                
                # Try locating by label
                labels = driver.find_elements(By.XPATH, 
                    f'//label[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{label_text.lower()}")]')
                
                for label in labels:
                    for_attr = label.get_attribute("for")
                    if for_attr:
                        try:
                            inp = driver.find_element(By.ID, for_attr)
                            if inp.is_displayed():
                                if inp.tag_name.lower() == "select":
                                    select = Select(inp)
                                    select.select_by_visible_text(str(value))
                                else:
                                    inp.clear()
                                    inp.send_keys(str(value))
                                return True
                        except:
                            continue
                    
                    # Find input inside the label
                    try:
                        inp = label.find_element(By.CSS_SELECTOR, "input, select, textarea")
                        if inp.is_displayed():
                            if inp.tag_name.lower() == "select":
                                select = Select(inp)
                                select.select_by_visible_text(str(value))
                            else:
                                inp.clear()
                                inp.send_keys(str(value))
                            return True
                    except:
                        continue
                        
            except Exception:
                continue
        
        return False
    
    def _take_full_page_screenshot(self, driver, screenshot_path: str):
        """Take a full page screenshot by scrolling and stitching"""
        from PIL import Image
        import io
        
        # Get the original window size
        original_size = driver.get_window_size()
        
        # Get the full page dimensions using JavaScript
        total_width = driver.execute_script("return Math.max(document.body.scrollWidth, document.body.offsetWidth, document.documentElement.clientWidth, document.documentElement.scrollWidth, document.documentElement.offsetWidth);")
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
        
        print(f"Full page dimensions: {total_width}x{total_height}")
        
        # Set window size to full page width (or max 1920px for reasonable size)
        # Chrome has a max window height of 32767px
        max_window_height = 32767
        max_window_width = 1920
        
        window_width = min(total_width, max_window_width)
        window_height = min(total_height, max_window_height)
        
        driver.set_window_size(window_width, window_height)
        time.sleep(1)  # Wait for resize
        
        # Get the actual viewport dimensions after resize
        viewport_height = driver.execute_script("return window.innerHeight")
        viewport_width = driver.execute_script("return window.innerWidth")
        
        # If the page fits in one screenshot, just take it
        if total_height <= viewport_height:
            driver.save_screenshot(screenshot_path)
        else:
            # Need to scroll and stitch
            screenshots = []
            scroll_position = 0
            
            while scroll_position < total_height:
                # Scroll to the current position
                driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(0.5)  # Wait for rendering
                
                # Take screenshot of current viewport
                screenshot_bytes = driver.get_screenshot_as_png()
                screenshot_img = Image.open(io.BytesIO(screenshot_bytes))
                screenshots.append((scroll_position, screenshot_img))
                
                # Calculate next scroll position
                next_position = scroll_position + viewport_height
                
                # If we've captured everything, break
                if next_position >= total_height:
                    break
                
                # Move to next position (with small overlap to ensure no gaps)
                scroll_position = next_position - 20  # 20px overlap
            
            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")
            
            # Stitch screenshots together
            if len(screenshots) == 1:
                screenshots[0][1].save(screenshot_path)
            else:
                # Create full screenshot
                full_screenshot = Image.new('RGB', (viewport_width, total_height), 'white')
                
                # Paste screenshots, handling overlap
                last_end = 0
                for i, (scroll_pos, img) in enumerate(screenshots):
                    # Calculate where to paste this image
                    # If there's overlap with previous image, start pasting after the overlap
                    paste_y = max(scroll_pos, last_end)
                    
                    # Calculate how much of this image to use
                    # If we're pasting after scroll_pos, we need to crop the top
                    crop_top = paste_y - scroll_pos
                    crop_bottom = img.height
                    
                    # If this extends beyond total height, crop the bottom
                    remaining_height = total_height - paste_y
                    if remaining_height < (img.height - crop_top):
                        crop_bottom = crop_top + remaining_height
                    
                    # Crop and paste
                    if crop_top > 0 or crop_bottom < img.height:
                        img_to_paste = img.crop((0, crop_top, img.width, crop_bottom))
                    else:
                        img_to_paste = img
                    
                    full_screenshot.paste(img_to_paste, (0, paste_y))
                    last_end = paste_y + img_to_paste.height
                
                full_screenshot.save(screenshot_path)
        
        # Restore original window size
        driver.set_window_size(original_size['width'], original_size['height'])
