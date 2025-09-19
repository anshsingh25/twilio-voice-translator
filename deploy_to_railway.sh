#!/bin/bash

echo "🚀 Deploying Fixed Twilio Voice Translator to Railway"
echo "=================================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    echo "   or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway first:"
    echo "   railway login"
    exit 1
fi

echo "✅ Railway CLI is ready"

# Set environment variables for Google Cloud
echo "🔧 Setting up environment variables..."

# Check if GOOGLE_APPLICATION_CREDENTIALS is set
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  GOOGLE_APPLICATION_CREDENTIALS not set"
    echo "   Please set it to your Google Cloud service account JSON file"
    echo "   Example: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/credentials.json"
fi

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Check your Railway dashboard for deployment status"
echo "2. Set environment variables in Railway dashboard:"
echo "   - GOOGLE_APPLICATION_CREDENTIALS (upload your JSON file)"
echo "3. Test the health endpoint: https://your-app.railway.app/health"
echo "4. Configure your Twilio webhook URL"
echo ""
echo "🔗 Your app should be available at: https://your-app.railway.app"
