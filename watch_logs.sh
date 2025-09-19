#!/bin/bash
echo "🔍 Watching Railway logs for your Twilio Voice Translator..."
echo "📞 Make a call to your Twilio number to see the logs!"
echo "Press Ctrl+C to stop watching"
echo "=================================================="

while true; do
    echo "🔄 Checking for new logs..."
    railway logs | tail -20
    echo "=================================================="
    sleep 5
done
