# Railway Volume Deployment Guide

This guide shows how to deploy your backend to Railway using volumes for data storage (the clean way).

## Prerequisites
- Railway CLI installed: `brew install railway` or `curl -fsSL https://railway.app/install.sh | sh`
- Railway account and project created

## Step 1: Deploy the Application First

1. **Update Procfile** to use the Railway-optimized version:
```bash
echo "web: uvicorn stream_cli_output_railway:app --host 0.0.0.0 --port \$PORT" > Procfile
```

2. **Commit just the code** (no data):
```bash
git add stream_cli_output_railway.py Procfile
git commit -m "Add Railway-optimized backend"
git push origin main
```

3. **Deploy to Railway**:
- Connect your GitHub repo
- Deploy from main branch
- Add environment variables (MOONSHOT_API_KEY, GROQ_API_KEY)

## Step 2: Add Volume and Upload Data

1. **Create a volume** in Railway dashboard:
- Go to your service
- Click "Settings" → "Volumes"
- Click "Create Volume"
- Name: `corpus-data`
- Mount path: `/app/data`

2. **Upload data using Railway CLI**:

```bash
# Login and link to your project
railway login
railway link

# Create directory structure in the volume
railway run mkdir -p /app/data/processed/enriched

# Upload all JSON files
railway run cp -r ../data/processed/enriched/* /app/data/processed/enriched/

# Verify upload
railway run ls -la /app/data/processed/enriched/ | head -10
```

## Step 3: Alternative - Upload via Script

Create `upload_to_railway.sh`:
```bash
#!/bin/bash
echo "Uploading interview data to Railway volume..."

# Upload each JSON file
for file in ../data/processed/enriched/*.json; do
    echo "Uploading $(basename $file)..."
    railway run cp "$file" /app/data/processed/enriched/
done

echo "Upload complete!"
railway run ls /app/data/processed/enriched/ | wc -l
```

## Step 4: Verify Deployment

1. **Check health endpoint**:
```bash
curl https://your-app.up.railway.app/health
```

Should return:
```json
{
  "status": "ok",
  "data_loaded": true,
  "data_path": "/app/data/processed/enriched",
  "file_count": 37
}
```

2. **Test data endpoint**:
```bash
curl https://your-app.up.railway.app/test-data
```

## Step 5: Update Frontend

In `cli-terminal.html`:
```javascript
const API_URL = 'https://your-app.up.railway.app';
```

## Advantages of This Approach

✅ **Clean git history** - No data files in repository  
✅ **Persistent storage** - Data survives deployments  
✅ **Easy updates** - Can update data without redeploying  
✅ **Professional** - Follows cloud best practices  
✅ **Scalable** - Can handle larger datasets  

## Troubleshooting

### Data not found?
```bash
# Check volume contents
railway run ls -la /app/data/processed/enriched/

# Check service logs
railway logs
```

### Permission issues?
```bash
# Set proper permissions
railway run chmod -R 755 /app/data
```

### Need to re-upload?
```bash
# Clear and re-upload
railway run rm -rf /app/data/processed/enriched/*
railway run cp -r ../data/processed/enriched/* /app/data/processed/enriched/
```