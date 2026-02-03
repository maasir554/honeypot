import requests
import time
import json

BASE_URL = "http://localhost:8000/api/chat"
API_KEY = "YOUR_SECRET_API_KEY" # Should match what's in env or arbitrary if no env check

def send_message(session_id, message, history=[]):
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": message,
            "timestamp": int(time.time() * 1000)
        },
        "conversationHistory": history,
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Sending: {message}")
        response = requests.post(BASE_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Agent Reply: {data['reply']}")
            return data['reply']
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def main():
    session_id = "sim-session-ind-001"
    history = []
    
    # 1. Initial Scam Hook
    print("\n--- Turn 1: Initial Hook ---")
    scam_msg = "Your SBI account is blocked due to KYC. Click http://bit.ly/update-kyc to verify immediately."
    reply = send_message(session_id, scam_msg, history)
    history.append({"sender": "scammer", "text": scam_msg, "timestamp": int(time.time() * 1000)})
    history.append({"sender": "user", "text": reply, "timestamp": int(time.time() * 1000)})
    print("...Waiting 15s to avoid Rate Limits...")
    time.sleep(15)

    # 2. Demand Call (Phone Extraction)
    print("\n--- Turn 2: Providing Phone Number ---")
    scam_msg = "Madam, please call our support agent at +91-98765-43210 to unblock immediately."
    reply = send_message(session_id, scam_msg, history)
    history.append({"sender": "scammer", "text": scam_msg, "timestamp": int(time.time() * 1000)})
    history.append({"sender": "user", "text": reply, "timestamp": int(time.time() * 1000)})
    time.sleep(2)
    
    # 3. Demand UPI (UPI Extraction) after Agent likely says call failed/confused
    print("\n--- Turn 3: Providing UPI ---")
    scam_msg = "Okay network issue. You can pay penalty Rs. 10 to reactivate. GPay to: kyc-verify@upi"
    reply = send_message(session_id, scam_msg, history)
    history.append({"sender": "scammer", "text": scam_msg, "timestamp": int(time.time() * 1000)})
    history.append({"sender": "user", "text": reply, "timestamp": int(time.time() * 1000)})
    time.sleep(2)

    # 4. Demand Bank Transfer (Bank Extraction) after Agent likely fails UPI
    print("\n--- Turn 4: Providing Bank Details ---")
    scam_msg = "UPI server down? Send IMPS to Manager Account: Acct 1234567890, IFSC SBIN0001234, Name: Rajesh Kumar."
    reply = send_message(session_id, scam_msg, history)
    # End of simulation
    print("\nSimulation Complete. Check conversation.log and extracted_intelligence.log")

if __name__ == "__main__":
    main()
