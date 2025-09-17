from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse

app = Flask(__name__)

# Endpoint that Twilio will call when someone dials your number
@app.route("/voice", methods=["POST"])
def voice():
    response = VoiceResponse()
    response.say("Hello! Your call is connected using Twilio and ngrok.", voice="alice")
    response.pause(length=1)
    response.say("Goodbye!", voice="alice")
    return Response(str(response), mimetype="application/xml")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
