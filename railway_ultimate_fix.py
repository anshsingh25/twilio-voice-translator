#!/usr/bin/env python3
"""
Railway Ultimate Fix - Working Call Forwarder
"""

from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "Call Forwarder Working"}, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Handle incoming calls and forward to your number"""
    try:
        call_sid = request.form.get('CallSid')
        from_number = request.form.get('From')
        
        print(f"📞 CALL FROM: {from_number}")
        print(f"   CallSid: {call_sid}")
        
        # Simple call forwarding
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you now.</Say>
    <Dial>
        <Number>+916358762776</Number>
    </Dial>
    <Say voice="alice" language="en-US">Call ended.</Say>
</Response>"""
        
        print("✅ Forwarding call to +916358762776")
        return Response(twiml, mimetype='text/xml')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return Response("<?xml version='1.0' encoding='UTF-8'?><Response><Say>Error occurred.</Say></Response>", mimetype='text/xml')

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    print(f"🚀 CALL FORWARDER WORKING on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)