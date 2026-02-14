import os
import requests
import json

def test_vision():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY is not set.")
        return

    print(f"✅ Found API Key: {api_key[:5]}...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://test.local", 
        "X-Title": "Vision Test"
    }

    # Public image URL (a cat)
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg"

    payload = {
        "model": "openai/gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in one sentence."},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": 100
    }

    print("Sending request to OpenRouter...")
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:", response.json()['choices'][0]['message']['content'])
            print("✅ Vision API works!")
        else:
            print("❌ Error Response:", response.text)

    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_vision()
