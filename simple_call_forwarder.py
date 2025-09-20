#!/usr/bin/env python3
"""
Simple Call Forwarder - Fix for call forwarding issue
This will definitely work for call forwarding
"""

import os
from flask import Flask, request, Response
from twilio.rest import Client

app = Flask(__name__)

# Your personal number
YOUR_NUMBER = "+916358762776"

# Setup Twilio client
def setup_twilio():
    # Use environment variables only (no hardcoded credentials)
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    if account_sid and auth_token:
        return Client(account_sid, auth_token)
    return None

twilio_client = setup_twilio()

@app.route('/')
def home():
    return {
        "message": "Simple Call Forwarder",
        "status": "Ready",
        "your_number": YOUR_NUMBER,
        "twilio_number": "+13254250468",
        "twilio_configured": twilio_client is not None,
        "webhook_url": "/twilio-webhook"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming calls and forward to your number"""
    try:
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        to_number = request.form.get('To')
        
        print(f"📞 INCOMING CALL:")
        print(f"   From: {from_number}")
        print(f"   To: {to_number}")
        print(f"   CallSid: {call_sid}")
        print("="*50)
        
        # Get Railway domain
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'your-app.railway.app')
        
        # Check if caller is your number (avoid loop)
        if from_number == YOUR_NUMBER:
            print("⚠️ Call from same number - avoiding loop")
            twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Sorry, cannot forward to the same number.</Say>
    <Hangup/>
</Response>"""
            return Response(twiml, mimetype='text/xml')
        
        # Simple call forwarding using TwiML Dial
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you now.</Say>
    <Dial timeout="30" record="true" recordingStatusCallback="https://{railway_domain}/recording-callback">
        <Number>{YOUR_NUMBER}</Number>
    </Dial>
    <Say voice="alice" language="en-US">Call ended.</Say>
</Response>"""
        
        print(f"✅ Forwarding call to {YOUR_NUMBER}")
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response><Say>Error occurred.</Say></Response>", mimetype='text/xml')

@app.route('/recording-callback', methods=['POST'])
def recording_callback():
    """Handle call recording"""
    try:
        call_sid = request.form.get('CallSid')
        recording_url = request.form.get('RecordingUrl')
        recording_duration = request.form.get('RecordingDuration')
        
        print(f"🎙️ RECORDING:")
        print(f"   CallSid: {call_sid}")
        print(f"   Duration: {recording_duration} seconds")
        print(f"   URL: {recording_url}")
        print("="*50)
        
        return {"status": "success"}, 200
        
    except Exception as e:
        print(f"❌ Recording error: {e}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 SIMPLE CALL FORWARDER on port {port}")
    print("="*50)
    print("✅ Features:")
    print(f"   ✓ Forwards calls to {YOUR_NUMBER}")
    print(f"   ✓ Twilio number: +13254250468")
    print(f"   ✓ Twilio configured: {twilio_client is not None}")
    print("   ✓ Simple and reliable")
    print("="*50)
    print("📞 Setup Instructions:")
    print("   1. Deploy to Railway")
    print("   2. Set webhook URL in Twilio Console:")
    print("      https://your-app.railway.app/twilio-webhook")
    print("   3. Test by calling +13254250468")
    print("="*50)
    
    app.run(host='0.0.0.0', port=port, debug=False)
