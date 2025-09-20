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
        
        # Create conference room
        conference_name = f"conf_{call_sid}"
        
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you to conference.</Say>
    <Dial>
        <Conference>{conference_name}</Conference>
    </Dial>
</Response>"""
        
        # Call your number to join conference
        import requests
        from twilio.rest import Client
        
        client = Client(
            os.environ.get('TWILIO_ACCOUNT_SID', 'AC9d0df83b641a03dc0dd1861f3663bf5b'),
            os.environ.get('TWILIO_AUTH_TOKEN', '2df00ce08d7c944719281aa84a4b070f')
        )
        
        # Call your number to join same conference
        client.calls.create(
            to=YOUR_NUMBER,
            from_="+13254250468",
            url=f"https://web-production-6577e.up.railway.app/join-conference?conf={conference_name}",
            method='POST'
        )
        
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"Error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response><Say>Error</Say></Response>", mimetype='text/xml')

@app.route('/join-conference', methods=['POST'])
def join_conference():
    """You join the conference"""
    conference_name = request.args.get('conf', 'default')
    
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">You are now connected to the caller.</Say>
    <Dial>
        <Conference>{conference_name}</Conference>
    </Dial>
</Response>"""
    
    return Response(twiml, mimetype='text/xml')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 CONFERENCE CALL FORWARDER on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
