#!/bin/bash
# Railway Deployment Script for Uruguay Interview Research Backend

echo "🚀 Starting Railway deployment process..."

# Check if we're in the right directory
if [ ! -f "stream_cli_output_simple.py" ]; then
    echo "❌ Error: Must run from search-mvp directory"
    exit 1
fi

# Create deployment branch
echo "📝 Creating deployment branch..."
git checkout -b railway-deploy-$(date +%Y%m%d-%H%M%S)

# Backup original .gitignore
echo "💾 Backing up .gitignore..."
cp .gitignore .gitignore.bak

# Create minimal .gitignore for deployment
echo "📄 Creating deployment .gitignore..."
cat > .gitignore << EOF
__pycache__/
*.pyc
.env
.env.local
.venv/
venv/
*.log
.DS_Store
EOF

# Add data files to git
echo "📦 Adding enriched data to git..."
git add -f data/processed/enriched/
git add -f .gitignore

# Update Procfile to use optimized version
echo "🔧 Updating Procfile..."
echo "web: uvicorn stream_cli_output_optimized:app --host 0.0.0.0 --port \$PORT" > Procfile
git add Procfile

# Add the optimized backend if it exists
if [ -f "stream_cli_output_optimized.py" ]; then
    git add stream_cli_output_optimized.py
fi

# Create railway.json
echo "🛤️ Creating railway.json..."
cat > railway.json << EOF
{
  "\$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn stream_cli_output_optimized:app --host 0.0.0.0 --port \$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
EOF
git add railway.json

# Create runtime.txt for Python version
echo "🐍 Setting Python version..."
echo "python-3.11.x" > runtime.txt
git add runtime.txt

# Commit all changes
echo "💾 Committing deployment files..."
git add -A
git commit -m "Prepare for Railway deployment with enriched corpus data"

# Push to GitHub
echo "📤 Pushing to GitHub..."
BRANCH_NAME=$(git branch --show-current)
git push origin $BRANCH_NAME

echo "✅ Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Go to https://railway.app"
echo "2. Create a new project"
echo "3. Deploy from GitHub -> Select branch: $BRANCH_NAME"
echo "4. Add environment variables:"
echo "   - MOONSHOT_API_KEY"
echo "   - GROQ_API_KEY (if using Groq)"
echo "5. Deploy!"
echo ""
echo "After deployment, update cli-terminal.html with your Railway URL"
echo ""
echo "To cleanup after demo:"
echo "  git checkout main"
echo "  mv .gitignore.bak .gitignore"
echo "  git branch -D $BRANCH_NAME"