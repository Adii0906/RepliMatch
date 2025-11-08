#!/bin/bash

# RepliMatch Startup Script
echo "🚀 Starting RepliMatch - Your Dev Soulmate Finder!"
echo "=================================================="

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Creating default..."
    cat > .env << EOF
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
FLASK_ENV=development
FLASK_DEBUG=1
GEMINI_API_KEY=your_gemini_api_key_here
EOF
    echo "✅ .env file created. Please update GEMINI_API_KEY with your actual API key."
fi

# Create uploads directory if it doesn't exist
mkdir -p static/uploads/profile_photos

# Start the Flask app
echo "✨ Starting Flask application..."
python app.py
