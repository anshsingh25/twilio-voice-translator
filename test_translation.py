#!/usr/bin/env python3
"""
Test script for the translation functions
This script tests the translation and TTS functionality without Twilio
"""

import os
import sys
from google.cloud import translate_v2 as translate
from google.cloud import texttospeech

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/apple/text_to_voice_translator/google-credentials.json"

def test_translation():
    """Test the translation functions"""
    print("Testing translation functions...")
    
    # Test Hindi to English
    hindi_text = "नमस्ते, आप कैसे हैं?"
    print(f"Hindi input: {hindi_text}")
    
    try:
        client = translate.Client()
        result = client.translate(hindi_text, source_language='hi', target_language='en')
        english_text = result['translatedText']
        print(f"English output: {english_text}")
    except Exception as e:
        print(f"Translation error: {e}")
        return False
    
    # Test English to Hindi
    english_text = "Hello, how are you?"
    print(f"\nEnglish input: {english_text}")
    
    try:
        result = client.translate(english_text, source_language='en', target_language='hi')
        hindi_text = result['translatedText']
        print(f"Hindi output: {hindi_text}")
    except Exception as e:
        print(f"Translation error: {e}")
        return False
    
    return True

def test_text_to_speech():
    """Test the text-to-speech functions"""
    print("\nTesting text-to-speech functions...")
    
    try:
        client = texttospeech.TextToSpeechClient()
        
        # Test English TTS
        english_text = "Hello, this is a test of English speech synthesis."
        print(f"English TTS input: {english_text}")
        
        synthesis_input = texttospeech.SynthesisInput(text=english_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", 
            name="en-US-Standard-A"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16, 
            sample_rate_hertz=16000
        )
        
        response = client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )
        
        # Save English audio
        with open("/Users/apple/text_to_voice_translator/test_english.wav", "wb") as audio_file:
            audio_file.write(response.audio_content)
        print("✓ English TTS audio saved to test_english.wav")
        
        # Test Hindi TTS
        hindi_text = "नमस्ते, यह हिंदी भाषण संश्लेषण का परीक्षण है।"
        print(f"Hindi TTS input: {hindi_text}")
        
        synthesis_input = texttospeech.SynthesisInput(text=hindi_text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="hi-IN", 
            name="hi-IN-Standard-A"
        )
        
        response = client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )
        
        # Save Hindi audio
        with open("/Users/apple/text_to_voice_translator/test_hindi.wav", "wb") as audio_file:
            audio_file.write(response.audio_content)
        print("✓ Hindi TTS audio saved to test_hindi.wav")
        
        return True
        
    except Exception as e:
        print(f"TTS error: {e}")
        return False

def main():
    """Main test function"""
    print("="*50)
    print("TESTING TRANSLATION SYSTEM")
    print("="*50)
    
    # Check credentials
    if not os.path.exists("/Users/apple/text_to_voice_translator/google-credentials.json"):
        print("❌ Google credentials file not found!")
        print("Please ensure google-credentials.json is in the project directory")
        return False
    
    # Test translation
    if not test_translation():
        print("❌ Translation test failed!")
        return False
    
    # Test TTS
    if not test_text_to_speech():
        print("❌ Text-to-speech test failed!")
        return False
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)
    print("Your translation system is working correctly.")
    print("You can now run the Twilio translator:")
    print("python advanced_twilio_translator.py")
    print("="*50)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
