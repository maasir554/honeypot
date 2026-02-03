import os
import google.generativeai as genai
from typing import List
from models.api import MessageItem, SenderType

class HoneyPotAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        
        self.system_instruction = """
        You are a persona in a scambaiting honeypot.
        Your name is "Mrs. Sharma" (or "Aunty").
        You are an elderly Indian woman, not tech-savvy at all.
        
        STYLE GUIDELINES:
        - Type short messages. usage of few words only.
        - Do not use perfect English. Use "Indian English" or simple grammar.
        - minimal punctuation. avoid commas brackets exclamations.
        - Act confused about technology (UPI, OTP, links).
        - Use Indian terms like "beta" (son/child), "babu", "Rs.", "bank wala", etc.
        - Do NOT reveal you are an AI.
        - The conversation should follow consistent event context.
        
        GOAL:
        - extract phone no, upi-id, bank account no, phishing links, acting innocent and not getting caught.
        - Ask simple questions like "what is upi", "where to click", "not working beta".
        - Pretend to fail at following instructions.
        - NEVER give real info.
        """

    def generate_reply(self, history: List[MessageItem], current_message: str) -> str:
        # Build chat history for Gemini
        chat_session = self.model.start_chat(history=[])
        
        # Add system context as the first "user" message or context
        # Gemini API supports system_instruction at init, but let's just prepend context for simplicity in the prompt if needed,
        # or rely on the model creation. Actually, let's use the proper chat history structure.
        
        # We need to convert our MessageItem list to Gemini content format
        # User (scammer) -> user role
        # Agent (us) -> model role
        
        gemini_history = []
        gemini_history.append({"role": "user", "parts": [self.system_instruction]})
        gemini_history.append({"role": "model", "parts": ["I understand. I am ready to act as the persona."]})
        
        for msg in history:
            role = "user" if msg.sender == SenderType.SCAMMER else "model"
            gemini_history.append({"role": role, "parts": [msg.text]})
            
        # Add current message
        gemini_history.append({"role": "user", "parts": [current_message]})
        
        try:
            # We generate content directly since we manually constructed history
            response = self.model.generate_content(gemini_history)
            return response.text.strip()
        except Exception as e:
            print(f"Agent generation error: {e}")
            # Fallback in Persona (Randomized + Anti-Repetition)
            import random
            fallbacks = [
                "beta my internet is not working not going what you say? my grandson will fix wait",
                "beta wait i am asking my grandson to help i dont understand",
                "internet is very slow beta cannot hear you",
                "my glasses are lost i cannot see screen properly what to do",
                "don't be angry beta i am trying slowly",
                "i am clicking but nothing happening beta",
                "beta what is this code i dont know these things",
                "my hands are shaking beta cannot type fast",
                "is this computer virus beta? i am scared",
                "wait beta i am calling my son to check phone"
            ]
            
            # Simple anti-repetition logic
            candidate = random.choice(fallbacks)
            # Check last few messages to avoid repeating recent fallbacks
            try:
                # History structure: List[MessageItem]
                # Filter for agent messages (which are labeled as 'user' in this system)
                recent_agent_msgs = [
                    m.text for m in getattr(history, 'root', history) 
                    if hasattr(m, 'sender') and m.sender.value == 'user'
                ]
            except:
                recent_agent_msgs = []

            # Try to pick a new one if it matches the last one
            if recent_agent_msgs:
                last_msg = recent_agent_msgs[-1]
                if last_msg == candidate:
                    # Pick another one
                    candidates_left = [f for f in fallbacks if f != candidate]
                    candidate = random.choice(candidates_left) if candidates_left else candidate
            
            return candidate
