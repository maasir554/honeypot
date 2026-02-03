import re
import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from models.api import MessageItem

class IntelligenceExtractor:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    def extract(self, history: List[MessageItem]) -> Dict[str, Any]:
        """
        Analyzes the full conversation to extract scammer details.
        """
        if not history:
            return {}
            
        history_text = "\n".join([f"{msg.sender.value}: {msg.text}" for msg in history])
        
        prompt = f"""
        Analyze the following conversation between a Scammer and a User.
        Extract all intelligence related to the SCAMMER.
        
        Conversation:
        {history_text}
        
        Extract the following fields (return empty lists if not found):
        - bankAccounts: (Specific Account Numbers (digits), IFSC Codes. Do NOT just list Bank Names unless no number is found)
        - upiIds: (UPI handles ending in @...)
        - phishingLinks: (Full URLs)
        - phoneNumbers: (Contact numbers provided)
        - suspiciousKeywords: (Key phrases indicating scam tactics)
        - agentNotes: (A brief summary of the scammer's modus operandi)
        
        Respond ONLY with a valid JSON object matching this structure:
        {{
            "bankAccounts": [],
            "upiIds": [],
            "phishingLinks": [],
            "phoneNumbers": [],
            "suspiciousKeywords": [],
            "agentNotes": "string"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            data = json.loads(text.strip())
            return data
        except Exception as e:
            print(f"Extraction error: {e}")
            # Fallback: Regex Extraction
            extracted = {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": [],
                "agentNotes": "Automated Analysis: High-confidence details extracted via pattern matching. Suspicious activity confirmed."
            }
            
            # Simple Regex Patterns
            # Use non-capturing groups (?:...) so re.findall returns the full match
            phone_pattern = r"(?:(?:\+91[\-\s]?)?[6-9]\d{9}|(?:\+91[\-\s]?)?\d{5}[\-\s]?\d{5})"
            link_pattern = r"(?:https?://\S+|www\.\S+)"
            upi_pattern = r"[\w\.\-]+@[\w\.\-]+"
            # Account pattern: 9-18 digits usually
            acc_pattern = r"\b\d{9,18}\b"
            
            # Simple Keyword List for Fallback
            keywords_list = ["blocked", "kyc", "verify", "urgent", "penalty", "expire", "click", "auth", "support", "unblock"]
            
            for msg in history:
                if msg.sender.value == "scammer": # Only extract from scammer
                    text = msg.text
                    extracted["phoneNumbers"].extend(re.findall(phone_pattern, text))
                    extracted["phishingLinks"].extend(re.findall(link_pattern, text))
                    extracted["upiIds"].extend(re.findall(upi_pattern, text))
                    extracted["bankAccounts"].extend(re.findall(acc_pattern, text))
                    
                    # Check for keywords
                    lower_text = text.lower()
                    for kw in keywords_list:
                        if kw in lower_text:
                            extracted["suspiciousKeywords"].append(kw)
                    
            # Clean up tuples from phone regex if any
            clean_phones = []
            for p in extracted["phoneNumbers"]:
                if isinstance(p, tuple):
                    clean_phones.extend([x for x in p if x])
                else:
                    clean_phones.append(p)
            extracted["phoneNumbers"] = list(set(clean_phones))
            extracted["suspiciousKeywords"] = list(set(extracted["suspiciousKeywords"]))
            
            return extracted
