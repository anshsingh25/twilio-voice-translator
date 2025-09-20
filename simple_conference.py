#!/usr/bin/env python3
"""
Simple Conference Call - No Complex Stuff
"""

from flask import Flask, request, Response

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "Simple Conference Ready"}, 200

@app.route('/twilio-webhook', methods=['POST'])
def twilio_webhook():
    """Simple conference call"""
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">Connecting you now.</Say>
    <Dial>
        <Number>+916358762776</Number>
    </Dial>
    <Say voice="alice" language="en-US">Call ended.</Say>
</Response>"""
    
    return Response(twiml, mimetype='text/xml')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=False)
