#!/bin/bash

# Railway startup script for Twilio Voice Translator

echo "Starting Twilio Bidirectional Voice Translator on Railway..."

# Check if Google credentials are provided
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Warning: GOOGLE_APPLICATION_CREDENTIALS not set"
    echo "Please set your Google Cloud credentials in Railway environment variables"
fi

# Start the application
python3 railway_translator.py
