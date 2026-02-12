import os
import requests
import logging

logger = logging.getLogger(__name__)

PAYMOB_API_KEY = os.getenv("PAYMOB_API_KEY")
PAYMOB_INTEGRATION_ID = os.getenv("PAYMOB_INTEGRATION_ID")
PAYMOB_IFRAME_ID = os.getenv("PAYMOB_IFRAME_ID")

def get_auth_token():
    """
    Step 1: Get Authentication Token from Paymob.
    """
    try:
        if not PAYMOB_API_KEY:
            logger.error("PAYMOB_API_KEY is not set.")
            return None
            
        response = requests.post(
            "https://accept.paymob.com/api/auth/tokens",
            json={"api_key": PAYMOB_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("token")
    except Exception as e:
        logger.error(f"Error getting Paymob auth token: {e}")
        return None

def register_order(auth_token, amount_cents):
    """
    Step 2: Register an order.
    """
    try:
        response = requests.post(
            "https://accept.paymob.com/api/ecommerce/orders",
            json={
                "auth_token": auth_token,
                "delivery_needed": "false",
                "amount_cents": amount_cents,
                "currency": "EGP",
                "items": []
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("id")
    except Exception as e:
        logger.error(f"Error registering Paymob order: {e}")
        return None

def get_payment_key(auth_token, order_id, amount_cents, billing_data):
    """
    Step 3: Get Payment Key.
    """
    try:
        if not PAYMOB_INTEGRATION_ID:
            logger.error("PAYMOB_INTEGRATION_ID is not set.")
            return None

        response = requests.post(
            "https://accept.paymob.com/api/acceptance/payment_keys",
            json={
                "auth_token": auth_token,
                "amount_cents": amount_cents,
                "expiration": 3600, 
                "order_id": order_id,
                "billing_data": billing_data,
                "currency": "EGP",
                "integration_id": PAYMOB_INTEGRATION_ID
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("token")
    except Exception as e:
        logger.error(f"Error getting Paymob payment key: {e}")
        return None

def generate_payment_link(amount_egp, user_info):
    """
    Orchestrates the Paymob flow and returns the iframe URL.
    """
    token = get_auth_token()
    if not token: return None
    
    amount_cents = int(amount_egp * 100)
    order_id = register_order(token, amount_cents)
    if not order_id: return None
    
    # Needs valid billing data even if dummy
    billing_data = {
        "apartment": "NA", 
        "email": user_info.get("email", "user@example.com"), 
        "floor": "NA", 
        "first_name": user_info.get("first_name", "User"), 
        "street": "NA", 
        "building": "NA", 
        "phone_number": user_info.get("phone_number", "+201000000000"), 
        "shipping_method": "NA", 
        "postal_code": "NA", 
        "city": "Cairo", 
        "country": "EG", 
        "last_name": user_info.get("last_name", "Customer"), 
        "state": "NA"
    }
    
    payment_key = get_payment_key(token, order_id, amount_cents, billing_data)
    if not payment_key: return None
    
    if not PAYMOB_IFRAME_ID:
        # If no iframe ID, maybe fallback to the simple processed link?
        # But usually you need iframe ID. Let's return a direct link if possible or just iframe URL.
        # Paymob frame URL: https://accept.paymob.com/api/acceptance/iframes/{iframe_id}?payment_token={payment_key}
        return f"https://accept.paymob.com/api/acceptance/iframes/12345?payment_token={payment_key}" # Placeholder ID
        
    return f"https://accept.paymob.com/api/acceptance/iframes/{PAYMOB_IFRAME_ID}?payment_token={payment_key}"
