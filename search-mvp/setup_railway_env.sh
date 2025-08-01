#!/bin/bash

# Script to set up Railway environment variables
# Run this after you've logged into Railway and initialized your project

echo "🚂 Setting up Railway environment variables..."
echo ""

# Check if user is logged into Railway
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Function to safely read API key
read_api_key() {
    local key_name=$1
    local key_value=""
    
    echo -n "Enter your $key_name (or press Enter to skip): "
    read -s key_value
    echo ""
    
    if [ ! -z "$key_value" ]; then
        railway variables set $key_name="$key_value"
        echo "✅ $key_name set successfully"
    else
        echo "⏭️  Skipped $key_name"
    fi
}

echo "📝 Please have your API keys ready. They will be hidden as you type."
echo ""

# Set MOONSHOT_API_KEY
read_api_key "MOONSHOT_API_KEY"

# Set GROQ_API_KEY
read_api_key "GROQ_API_KEY"

# Set Python version (optional but recommended)
echo ""
echo "🐍 Setting Python version to 3.11..."
railway variables set PYTHON_VERSION="3.11"

echo ""
echo "✅ Environment variables setup complete!"
echo ""
echo "📋 To verify your variables, run:"
echo "   railway variables"
echo ""
echo "🚀 To deploy your app, run:"
echo "   railway up"
echo ""
echo "🌐 After deployment, get your URL with:"
echo "   railway open"