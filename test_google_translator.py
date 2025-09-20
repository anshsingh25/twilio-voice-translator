#!/usr/bin/env python3
"""
Test Google Voice Translator
Simple test script to try the Google Cloud solution
"""

import requests
import json
import time

def test_translate_text():
    """Test text translation"""
    print("🧪 Testing text translation...")
    
    # Test data
    test_cases = [
        "Hello, how are you?",
        "नमस्ते, आप कैसे हैं?",
        "What is your name?",
        "आपका नाम क्या है?"
    ]
    
    for text in test_cases:
        print(f"\n📝 Testing: '{text}'")
        
        try:
            response = requests.post(
                'http://localhost:3000/translate-text',
                json={'text': text},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Translation: '{result['translated_text']}'")
                print(f"   Source: {result['source_language']} → Target: {result['target_language']}")
                print(f"   Audio generated: {len(result['audio_base64'])} bytes")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
        
        time.sleep(1)

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    
    try:
        response = requests.get('http://localhost:3000/health')
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health: {result['status']}")
            print(f"   Google Cloud: {result['google_cloud_available']}")
            print(f"   Credentials: {result['credentials_setup']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def main():
    print("🚀 Google Voice Translator Test")
    print("="*50)
    
    # Test health first
    test_health()
    print()
    
    # Test text translation
    test_translate_text()
    
    print("\n" + "="*50)
    print("✅ Test completed!")
    print("\n📞 To test audio recording:")
    print("   curl -X POST http://localhost:3000/start-recording")
    print("   (Speak for 5 seconds)")
    print("   curl -X POST http://localhost:3000/stop-recording")

if __name__ == "__main__":
    main()
