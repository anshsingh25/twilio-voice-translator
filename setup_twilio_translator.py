#!/usr/bin/env python3
"""
Setup script for Twilio Bidirectional Voice Translator
This script helps you configure and run the voice translation system.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        'flask',
        'websockets',
        'google-cloud-speech',
        'google-cloud-texttospeech',
        'google-cloud-translate',
        'pyaudio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} - MISSING")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✓ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"✗ Failed to install {package}")
                return False
    
    return True

def check_google_credentials():
    """Check if Google Cloud credentials are properly configured"""
    print("\nChecking Google Cloud credentials...")
    
    creds_path = "/Users/apple/text_to_voice_translator/google-credentials.json"
    
    if not os.path.exists(creds_path):
        print(f"✗ Google credentials file not found at {creds_path}")
        print("Please download your Google Cloud service account key and save it as 'google-credentials.json'")
        return False
    
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in creds:
                print(f"✗ Missing field '{field}' in credentials file")
                return False
        
        print("✓ Google Cloud credentials are valid")
        return True
        
    except json.JSONDecodeError:
        print("✗ Invalid JSON in credentials file")
        return False
    except Exception as e:
        print(f"✗ Error reading credentials: {e}")
        return False

def check_ngrok():
    """Check if ngrok is installed and running"""
    print("\nChecking ngrok...")
    
    try:
        # Check if ngrok is installed
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ ngrok is installed")
        else:
            print("✗ ngrok is not installed")
            print("Please install ngrok from https://ngrok.com/download")
            return False
        
        # Check if ngrok is running
        try:
            import requests
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            if response.status_code == 200:
                tunnels = response.json()
                if tunnels.get('tunnels'):
                    for tunnel in tunnels['tunnels']:
                        if tunnel['proto'] == 'https':
                            print(f"✓ ngrok tunnel active: {tunnel['public_url']}")
                            return tunnel['public_url']
                else:
                    print("✗ No active ngrok tunnels found")
            else:
                print("✗ ngrok API not responding")
        except Exception as e:
            print(f"✗ Error checking ngrok status: {e}")
        
        print("Please start ngrok with: ngrok http 3000")
        return False
        
    except FileNotFoundError:
        print("✗ ngrok command not found")
        print("Please install ngrok from https://ngrok.com/download")
        return False

def update_ngrok_url(ngrok_url):
    """Update the ngrok URL in the translator files"""
    print(f"\nUpdating ngrok URL to: {ngrok_url}")
    
    files_to_update = [
        'bidirectional_twilio_translator.py',
        'advanced_twilio_translator.py'
    ]
    
    for filename in files_to_update:
        filepath = f"/Users/apple/text_to_voice_translator/{filename}"
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Replace the placeholder URL
                updated_content = content.replace(
                    'wss://YOUR_NGROK_URL.ngrok-free.app/websocket',
                    f'wss://{ngrok_url.replace("https://", "")}/websocket'
                )
                
                with open(filepath, 'w') as f:
                    f.write(updated_content)
                
                print(f"✓ Updated {filename}")
                
            except Exception as e:
                print(f"✗ Error updating {filename}: {e}")

def create_twilio_config():
    """Create a configuration file with Twilio setup instructions"""
    config = {
        "twilio_setup": {
            "webhook_url": "http://YOUR_NGROK_URL.ngrok-free.app/twilio-webhook",
            "status_callback_url": "http://YOUR_NGROK_URL.ngrok-free.app/call-status",
            "instructions": [
                "1. Go to your Twilio Console",
                "2. Navigate to Phone Numbers > Manage > Active numbers",
                "3. Click on your phone number",
                "4. Set the webhook URL to your ngrok URL + /twilio-webhook",
                "5. Set HTTP method to POST",
                "6. Save the configuration"
            ]
        },
        "features": {
            "bidirectional_translation": "Hindi ↔ English",
            "voice_activity_detection": "Automatic speech detection",
            "language_detection": "Auto-detect Hindi/English",
            "real_time_processing": "Low latency translation"
        }
    }
    
    config_path = "/Users/apple/text_to_voice_translator/twilio_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Created configuration file: {config_path}")

def main():
    """Main setup function"""
    print("="*60)
    print("TWILIO BIDIRECTIONAL VOICE TRANSLATOR SETUP")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Setup failed: Missing dependencies")
        return False
    
    # Check Google credentials
    if not check_google_credentials():
        print("\n❌ Setup failed: Google Cloud credentials issue")
        return False
    
    # Check ngrok
    ngrok_url = check_ngrok()
    if not ngrok_url:
        print("\n⚠️  ngrok not running. Please start it with: ngrok http 3000")
        print("Then run this setup script again.")
        return False
    
    # Update ngrok URL in files
    update_ngrok_url(ngrok_url)
    
    # Create configuration file
    create_twilio_config()
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Configure your Twilio phone number webhook:")
    print(f"   URL: {ngrok_url}/twilio-webhook")
    print("   Method: POST")
    print("\n2. Run the translator:")
    print("   python advanced_twilio_translator.py")
    print("\n3. Make a call to your Twilio number")
    print("\n4. Test the bidirectional translation:")
    print("   - Speak in Hindi → hear English translation")
    print("   - Speak in English → hear Hindi translation")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
