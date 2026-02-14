import requests
import os
import json
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

def call_send_api(sender_id, message_data):
    """
    Sends response messages via the Send API.
    """
    if not PAGE_ACCESS_TOKEN:
        logger.error("PAGE_ACCESS_TOKEN is missing!")
        return

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
    
    try:
        r = requests.post("https://graph.facebook.com/v15.0/me/messages", params=params, headers=headers, json=payload)
        
        if r.status_code != 200:
            logger.error(f"Error sending message: {r.status_code}, {r.text}")
        else:
            logger.info(f"Message sent to {sender_id}")
    except Exception as e:
        logger.error(f"Exception sending message: {e}")

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
        logger.error(f"Error sending file: {r.status_code}, {r.text}")

def send_image(sender_id, image_path):
    """
    Sends an image to the user.
    """
    if not PAGE_ACCESS_TOKEN:
        logger.error("PAGE_ACCESS_TOKEN is missing")
        return

    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    
    data = {
        "recipient": json.dumps({"id": sender_id}),
        "message": json.dumps({
            "attachment": {
                "type": "image", 
                "payload": {}
            }
        })
    }
    
    # Prepare the file
    # Determine mime type (simple check)
    mime_type = "image/png"
    if image_path.lower().endswith(".jpg") or image_path.lower().endswith(".jpeg"):
        mime_type = "image/jpeg"
        
    try:
        files = {
            "filedata": (os.path.basename(image_path), open(image_path, "rb"), mime_type)
        }
        
        r = requests.post("https://graph.facebook.com/v15.0/me/messages", params=params, data=data, files=files)
        
        if r.status_code != 200:
            logger.error(f"Error sending image: {r.status_code}, {r.text}")
        else:
            logger.info(f"Image sent to {sender_id}")
    except Exception as e:
        logger.error(f"Exception sending image: {e}")
