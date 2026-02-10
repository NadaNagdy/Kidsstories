import requests
import os
import json

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "EAAMnq3oO86EBQsVinU1y5IEymoUYCF8NOsSUEsdt6IxrLJ1HVpB9F23VZAjKg6VrZBDM0Pg5CBOmwsC2ejeT3QYgyhIKFXGVdaEv4Tmtu7ScFNh04H23V5ZAtaveWZAXZCUxxmEFC8KVQQX8S0FylRUa8ZBbMJKKAWg0BRal7AkftZBZCh6rlE2SjGjgNpn35pQQarCOTci5I2ZBvbCPnrLyyxz0Q4h78rWhZAgeL3a7EJVbUf41cPZAOtZBpw4ZD")

def call_send_api(sender_id, message_data):
    """
    Sends response messages via the Send API.
    """
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "recipient": {"id": sender_id},
        "message": message_data
    }
    
    r = requests.post("https://graph.facebook.com/v15.0/me/messages", params=params, headers=headers, json=payload)
    
    if r.status_code != 200:
        print(f"Error sending message: {r.status_code}, {r.text}")

def send_text_message(sender_id, text):
    """
    Sends a simple text message.
    """
    message_data = {
        "text": text
    }
    call_send_api(sender_id, message_data)

def send_quick_replies(sender_id, text, options):
    """
    Sends quick reply buttons.
    options: list of strings (titles)
    """
    quick_replies = []
    for option in options:
        quick_replies.append({
            "content_type": "text",
            "title": option,
            "payload": option
        })
        
    message_data = {
        "text": text,
        "quick_replies": quick_replies
    }
    call_send_api(sender_id, message_data)

def send_file(sender_id, file_path):
    """
    Sends a file (PDF) to the user.
    """
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    
    data = {
        "recipient": json.dumps({"id": sender_id}),
        "message": json.dumps({
            "attachment": {
                "type": "file", 
                "payload": {}
            }
        })
    }
    
    # Prepare the file
    files = {
        "filedata": (os.path.basename(file_path), open(file_path, "rb"), "application/pdf")
    }
    
    r = requests.post("https://graph.facebook.com/v15.0/me/messages", params=params, data=data, files=files)
    
    if r.status_code != 200:
        print(f"Error sending file: {r.status_code}, {r.text}")
