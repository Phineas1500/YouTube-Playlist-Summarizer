# Modal Deployment Guide

This guide will help you deploy the YouTube Playlist Processor Modal app separately from your existing Modal applications.

## 📋 Prerequisites

1. **Modal CLI installed and authenticated**:
   ```bash
   pip install modal
   modal token set
   ```

2. **Verify your current Modal apps**:
   ```bash
   modal app list
   ```

## 🚀 Deploy the New Modal App

### 1. Deploy the YouTube Playlist Processor App

```bash
# Deploy the new Modal app (this creates a separate app)
modal deploy modal_app.py
```

This will create a new Modal app called `youtube-playlist-processor` that's completely separate from your existing Modal apps.

### 2. Verify Deployment

```bash
# List all your Modal apps to confirm the new one is deployed
modal app list

# You should see something like:
# - your-existing-app
# - youtube-playlist-processor  ← Your new app
```

### 3. Test the New App

```bash
# Test the new app locally
modal run modal_app.py

# Test a specific function
modal run modal_app.py::process_audio --help
```

## 🔧 App Structure

Your Modal apps are now organized like this:

```
Modal Account
├── your-existing-app/          # Your current app (unchanged)
│   ├── existing-function-1
│   └── existing-function-2
│
└── youtube-playlist-processor/  # New dedicated app
    └── process_audio           # Whisper transcription function
```

## 🔄 How It Works

1. **Separate Namespaces**: Each Modal app has its own namespace
2. **Independent Scaling**: Apps scale independently
3. **Isolated Resources**: No interference between apps
4. **Separate Billing**: Each app is billed separately

## 📝 Configuration

The new app is configured with:

- **App Name**: `youtube-playlist-processor`
- **GPU**: T4 (cost-efficient for Whisper)
- **Memory**: 8GB
- **Timeout**: 1 hour (for long videos)
- **Dependencies**: Whisper, PyTorch, etc.

## 🛠 Managing Multiple Apps

### Switch Between Apps
```bash
# Work with your existing app
modal app logs your-existing-app

# Work with the playlist processor app
modal app logs youtube-playlist-processor
```

### Update the Playlist Processor App
```bash
# Make changes to modal_app.py, then redeploy
modal deploy modal_app.py
```

### Stop/Start Apps
```bash
# Stop the playlist processor app (saves costs)
modal app stop youtube-playlist-processor

# Start it again when needed
modal deploy modal_app.py
```

## 💰 Cost Management

- **Your existing app**: Continues running as before
- **New app**: Only incurs costs when processing videos
- **Auto-scaling**: Both apps scale to zero when not in use

## 🔍 Monitoring

### View Logs
```bash
# Playlist processor logs
modal app logs youtube-playlist-processor

# Real-time logs during processing
modal app logs youtube-playlist-processor --follow
```

### Check Function Status
```bash
# List functions in the new app
modal app show youtube-playlist-processor
```

## 🚨 Troubleshooting

### "App not found" Error
```bash
# Redeploy the app
modal deploy modal_app.py

# Check if it's listed
modal app list
```

### Function Lookup Fails
```bash
# Make sure the app is deployed
modal app show youtube-playlist-processor

# If not found, deploy again
modal deploy modal_app.py
```

### Permission Issues
```bash
# Re-authenticate if needed
modal token set

# Check your account
modal profile current
```

## ✅ Verification Checklist

- [ ] Modal CLI installed and authenticated
- [ ] New app deployed: `modal deploy modal_app.py`
- [ ] App listed: `modal app list` shows `youtube-playlist-processor`
- [ ] Function accessible: `modal app show youtube-playlist-processor`
- [ ] Existing app unchanged: Your other app still works normally

## 🔄 Integration

Once deployed, the `modal_processor.py` script will automatically connect to your new `youtube-playlist-processor` app when the Node.js server processes videos.

The connection happens via:
```python
app = modal.App.lookup("youtube-playlist-processor")
process_audio_fn = app.with_name("process_audio")
```

This ensures complete separation from your existing Modal applications! 