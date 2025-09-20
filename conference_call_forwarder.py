#!/usr/bin/env python3
"""
Conference Call Forwarder - FAST SOLUTION
Caller + You = Conference call
"""

import os
from flask import Flask, request, Response

app = Flask(__name__)

YOUR_NUMBER = "+916358762776"

@app.route('/')
def home():
    return {"status": "Conference Call Forwarder Ready"}, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Create conference call between caller and you"""
    try:
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        
        print(f"📞 Conference call from: {from_number}")
        
        # Simple 3-way call - Direct dial to your number
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you now.</Say>
    <Dial>
        <Number>{YOUR_NUMBER}</Number>
    </Dial>
    <Say voice="alice" language="en-US">Call ended.</Say>
</Response>"""
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"Error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response><Say>Error</Say></Response>", mimetype='text/xml')


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 CONFERENCE CALL FORWARDER on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
