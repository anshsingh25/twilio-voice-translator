#!/usr/bin/env python3
"""
Railway Ultimate Fix - Simple Call Forwarder
This will definitely work
"""

import os
from flask import Flask, request, Response

app = Flask(__name__)

# Your personal number
YOUR_NUMBER = "+916358762776"

@app.route('/')
def home():
    return {
        "message": "Call Forwarder - WORKING",
        "status": "Ready",
        "your_number": YOUR_NUMBER,
        "twilio_number": "+13254250468"
    }, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming calls and forward to your number"""
    try:
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        
        print(f"📞 CALL FROM: {from_number}")
        print(f"   CallSid: {call_sid}")
        print(f"   Forwarding to: {YOUR_NUMBER}")
        
        # Simple call forwarding using TwiML Dial
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you now.</Say>
    <Dial timeout="30">
        <Number>{YOUR_NUMBER}</Number>
    </Dial>
    <Say voice="alice" language="en-US">Call ended.</Say>
</Response>"""
        
        print(f"✅ Forwarding call to {YOUR_NUMBER}")
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response><Say>Error occurred.</Say></Response>", mimetype='text/xml')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 CALL FORWARDER WORKING on port {port}")
    print(f"✅ Forwards calls to {YOUR_NUMBER}")
    
    app.run(host='0.0.0.0', port=port, debug=False)
