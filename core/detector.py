import os
import json
from groq import Groq
from typing import List
from models.api import MessageItem

class ScamDetector:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")
        self.client = Groq(api_key=api_key)
        self.model_name = "moonshotai/kimi-k2-instruct"

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
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a scam detection API. You only output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model_name,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            text = chat_completion.choices[0].message.content.strip()
            
            # Clean response if it contains markdown code blocks (Groq might treat response_format strictly, but safety first)
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
