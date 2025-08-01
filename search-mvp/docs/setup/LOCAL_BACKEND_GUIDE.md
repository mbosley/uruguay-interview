# Using Your Computer as Backend for Hosted Frontend

## Quick Setup with ngrok (Recommended)

### 1. Install ngrok
```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

### 2. Start Your Local Backend
```bash
cd /Users/mitchellbosley/projects/uruguay-interview/search-mvp
python stream_cli_output_simple.py
# Backend running at http://localhost:8001
```

### 3. Expose with ngrok
```bash
# In a new terminal
ngrok http 8001
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8001
```

### 4. Update Your Frontend
In `cli-terminal.html`:
```javascript
const API_URL = 'https://abc123.ngrok.io';  // Your ngrok URL
```

### 5. Push Frontend to GitHub Pages
```bash
git add cli-terminal.html
git commit -m "Update API URL to ngrok endpoint"
git push
```

## Alternative: Cloudflare Tunnel (More Stable)

### 1. Install Cloudflare Tunnel
```bash
brew install cloudflare/cloudflare/cloudflared
```

### 2. Create Tunnel
```bash
cloudflared tunnel --url http://localhost:8001
```

This gives you a stable URL like: `https://something.trycloudflare.com`

## Alternative: Tailscale (Private Access)

If you only need access from your own devices:

### 1. Install Tailscale
```bash
# Install from https://tailscale.com/download
```

### 2. Get Your Tailscale IP
```bash
tailscale ip -4
# e.g., 100.64.1.2
```

### 3. Update Frontend
```javascript
const API_URL = 'http://100.64.1.2:8001';  // Your Tailscale IP
```

## Important Considerations

### Security
- ngrok URLs are public (anyone can access)
- Add basic auth if needed:
  ```bash
  ngrok http 8001 --basic-auth="user:password"
  ```

### Reliability
- Backend only works when your computer is on
- Connection drops if computer sleeps
- ngrok free tier has limits (40 connections/minute)

### Performance
- Depends on your internet upload speed
- Add caching headers to reduce load

## Quick Test

1. Start backend: `python stream_cli_output_simple.py`
2. Start ngrok: `ngrok http 8001`
3. Test: `curl https://your-ngrok-url.ngrok.io/health`
4. Update frontend with ngrok URL
5. Access your GitHub Pages site

## Keeping It Running

To keep backend running even when terminal closes:
```bash
# Using nohup
nohup python stream_cli_output_simple.py > backend.log 2>&1 &

# Using screen
screen -S backend
python stream_cli_output_simple.py
# Ctrl+A, D to detach

# Using tmux
tmux new -s backend
python stream_cli_output_simple.py
# Ctrl+B, D to detach
```

## Stop Commands
```bash
# Find process
ps aux | grep stream_cli_output

# Kill process
kill [PID]

# Or killall
killall python
```