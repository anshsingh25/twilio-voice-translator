#!/bin/bash
# Railway Environment Variables Setup
# Run this script to set up your Railway environment variables

echo "🚀 Setting up Railway Environment Variables for Call Forwarding"
echo "=============================================================="

# Set Twilio credentials
echo "Setting TWILIO_ACCOUNT_SID..."
railway variables set TWILIO_ACCOUNT_SID="YOUR_ACCOUNT_SID_HERE"

echo "Setting TWILIO_AUTH_TOKEN..."
railway variables set TWILIO_AUTH_TOKEN="YOUR_AUTH_TOKEN_HERE"

echo "Setting TWILIO_PHONE_NUMBER..."
railway variables set TWILIO_PHONE_NUMBER="+13254250468"

echo "Setting PORT..."
railway variables set PORT="3000"

echo ""
echo "✅ Environment variables set successfully!"
echo ""
echo "📞 Next Steps:"
echo "1. Deploy your app: git push origin main"
echo "2. Get your Railway URL from Railway dashboard"
echo "3. Update Twilio webhook URL:"
echo "   https://your-app.railway.app/twilio-webhook"
echo "4. Test by calling +13254250468"
echo ""
echo "🎯 Your call forwarding will work now!"
