import os
import json
import google.generativeai as genai
from typing import List
from models.api import MessageItem

class ScamDetector:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        # Using Gemini 2.0 Flash as requested
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def detect(self, message: str, history: List[MessageItem]) -> bool:
        """
        Detects if the incoming message is a scam or has scam intent.
        Considers conversation history for context.
        """
        
        # Format history for context
        history_text = "\n".join([f"{msg.sender.value}: {msg.text}" for msg in history])
        
        prompt = f"""
        You are an expert scam detection system. Analyze the following message and conversation context.
        Determine if the latest message exhibits scam intent (phishing, fraud, social engineering, urgency, financial request, etc.).
        
        Context:
        {history_text}
        
        Latest Message to Analyze:
        "{message}"
        
        Respond ONLY with a valid JSON object:
        {{
            "is_scam": boolean,
            "confidence": float (0.0 to 1.0),
            "reason": "short explanation"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Clean response if it contains markdown code blocks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text.strip())
            return result.get("is_scam", False)
            
        except Exception as e:
            print(f"Error in scam detection: {e}")
            # Fail safe: For Honeypot, if API fails, assume it IS a scam so we capture intelligence.
            return True
