#!/usr/bin/env python3
"""
Railway Deployment - Simple Fixed Twilio Voice Translator
Simplified version without WebSocket for Railway deployment
"""

import os
import json
import time
import warnings
from flask import Flask, request, Response
import gunicorn.app.base

# Suppress pkg_resources deprecation warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
warnings.filterwarnings("ignore", category=UserWarning, module="google.cloud.translate_v2")

# Try to import Google Cloud libraries with error handling
try:
    from google.cloud import speech
    from google.cloud import texttospeech
    from google.cloud import translate_v2 as translate
    GOOGLE_CLOUD_AVAILABLE = True
    print("Google Cloud libraries imported successfully")
except ImportError as e:
    print(f"Google Cloud libraries not available: {e}")
    GOOGLE_CLOUD_AVAILABLE = False

# Flask app for HTTP webhooks
app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    status = {
        "status": "healthy", 
        "service": "twilio-voice-translator",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "port": os.environ.get('PORT', 'not_set'),
        "timestamp": time.time(),
        "version": "4.0-simple-fix"
    }
    return status, 200

@app.route('/')
def home():
    """Home endpoint"""
    return {
        "message": "Twilio Voice Translator is running!",
        "health_check": "/health",
        "webhook": "/twilio-webhook",
        "google_cloud_available": GOOGLE_CLOUD_AVAILABLE,
        "version": "4.0-simple-fix"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming Twilio calls"""
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    print(f"Incoming call from {from_number} to {to_number} (CallSid: {call_sid})")
    
    # Simple TwiML response without WebSocket
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say language="hi-IN">नमस्ते! मैं आपकी आवाज़ का अनुवाद करूंगा।</Say>
        <Say language="en-US">Hello! I will translate your voice.</Say>
        <Say language="hi-IN">अब आप बोल सकते हैं।</Say>
        <Say language="en-US">You can start speaking now.</Say>
        <Say language="hi-IN">यह एक सरल अनुवाद सेवा है।</Say>
        <Say language="en-US">This is a simple translation service.</Say>
        <Say language="hi-IN">धन्यवाद!</Say>
        <Say language="en-US">Thank you!</Say>
        <Hangup/>
    </Response>"""
    
    return Response(twiml, mimetype='text/xml')

@app.route('/call-status', methods=['POST'])
def call_status():
    """Handle call status updates"""
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    print(f"Call {call_sid} status: {call_status}")
    
    return Response('OK', mimetype='text/plain')

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """Gunicorn application for Railway deployment"""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()
    
    def load_config(self):
        config = {key: value for key, value in self.options.items()
                 if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)
    
    def load(self):
        return self.application

if __name__ == "__main__":
    try:
        # Get port from Railway environment variable
        port = int(os.environ.get('PORT', 3000))
        print(f"Starting Railway deployment on port {port}")
        print("="*70)
        print("RAILWAY TWILIO VOICE TRANSLATOR - SIMPLE FIX")
        print("="*70)
        print("Features:")
        print("✓ Simple voice response (no WebSocket)")
        print("✓ Railway cloud deployment")
        print("✓ Health check endpoint")
        print("✓ Gunicorn WSGI server")
        print(f"✓ Google Cloud available: {GOOGLE_CLOUD_AVAILABLE}")
        print(f"✓ Port: {port}")
        print("="*70)
        
        if not GOOGLE_CLOUD_AVAILABLE:
            print("WARNING: Google Cloud libraries not available!")
            print("Please check your GOOGLE_APPLICATION_CREDENTIALS environment variable")
        
        # Start Flask app with Gunicorn
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 1,
            'worker_class': 'sync',
            'worker_connections': 1000,
            'timeout': 30,
            'keepalive': 2,
            'max_requests': 1000,
            'max_requests_jitter': 100,
            'preload_app': True,
        }
        
        StandaloneApplication(app, options).run()
        
    except KeyboardInterrupt:
        print("Server stopped by user.")
    except Exception as e:
        print(f"Server startup error: {e}")
        import traceback
        traceback.print_exc()
