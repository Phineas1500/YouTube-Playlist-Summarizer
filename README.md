# YouTube Playlist Project Analyzer

An intelligent tool that analyzes YouTube playlists containing student project presentations, extracts auto-generated captions, and uses Google's Gemini AI to identify and summarize all mentioned projects.

## 🎯 What it does

1. **Fetches playlist videos** using YouTube Data API v3
2. **Extracts English auto-generated captions** from all videos
3. **Analyzes content with Gemini AI** to identify student projects
4. **Generates comprehensive summaries** of projects, technologies, and achievements
5. **Handles large datasets** with intelligent chunking and rate limiting

## 🚀 Features

- **Smart Rate Limiting**: Respects YouTube API and Gemini API limits
- **Resume Capability**: Can resume interrupted analysis sessions
- **Progress Tracking**: Saves progress every 10 videos processed
- **Chunking Support**: Handles large caption datasets by splitting into manageable chunks
- **Comprehensive Analysis**: Identifies projects, technologies, student names, and achievements
- **Error Handling**: Gracefully handles unavailable captions and API errors

## 📋 Prerequisites

### 1. YouTube Data API v3 Key
- Go to [Google Cloud Console](https://console.developers.google.com/)
- Create a new project or select existing one
- Enable YouTube Data API v3
- Create credentials (API Key)
- Note: Has generous free tier (10,000 units/day)

### 2. Gemini API Key
- Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
- Generate an API key
- Note: You mentioned having 1000 RPM limit

## 🛠️ Installation

1. **Clone or download the project files**

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
# Copy the example file
cp env_example.txt .env

# Edit .env with your API keys
nano .env
```

Add your API keys to the `.env` file:
```
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🎮 Usage

### Advanced Usage
```bash
python advanced_analyzer.py
```

The advanced version includes:
- Better rate limiting
- Progress saving/resuming
- Content chunking for large datasets
- Enhanced error handling

### Example Workflow

1. **Run the script:**
```bash
python advanced_analyzer.py
```

2. **Enter your playlist URL when prompted:**
```
Enter YouTube playlist URL: https://www.youtube.com/playlist?list=PLrAXtmRdnEQy...
```

3. **Choose whether to resume previous progress:**
```
Resume from previous progress if available? (y/n, default: y): y
```

4. **Wait for analysis to complete** (progress bars will show current status)

5. **Results will be saved** to `project_analysis_YYYYMMDD_HHMMSS.txt`

## 📊 Expected Output

The analyzer will generate a comprehensive report including:

### Executive Summary
- Top 5-10 most significant projects
- Overall themes and trends

### Detailed Project List
For each project:
- Project name/title
- Brief description
- Technologies and tools used
- Student name(s) (if mentioned)
- Notable achievements or results

### Technology Trends
- Most frequently mentioned technologies
- Popular frameworks and tools
- Programming languages used

### Notable Achievements
- Competition wins
- Published projects
- Significant milestones

## ⚡ Performance & Limitations

### YouTube API Limits
- **Daily Quota**: 10,000 units (generous for most playlists)
- **Cost per video**: ~3-4 units (playlist fetch + caption download)
- **~60 videos**: Uses approximately 200-250 units

### Gemini API Limits
- **Your limit**: 1000 RPM
- **Typical usage**: 1-10 requests depending on content size
- **Chunking**: Automatically splits large content

### Processing Time
- **~60 videos**: 10-30 minutes depending on:
  - Video length
  - Caption availability
  - Content size
  - API response times

## 🔧 Troubleshooting

### Common Issues

**"Captions not available (forbidden)"**
- Some videos have disabled auto-captions
- Private/unlisted videos may restrict caption access
- The script will skip these and continue

**"Rate limit reached"**
- The script automatically handles rate limiting
- Will pause and resume when limits reset

**"Invalid playlist URL"**
- Ensure URL contains `list=` parameter
- Example: `https://www.youtube.com/playlist?list=PLrAXtmRdnEQy...`

**"API key not found"**
- Check your `.env` file exists and has correct format
- Verify API keys are correct and active

### Resume Interrupted Analysis
If the script stops unexpectedly:
1. Run it again with the same playlist URL
2. Choose "y" when asked about resuming
3. It will continue from where it left off

### Large Playlists
For playlists with 100+ videos:
- Use the advanced analyzer (`advanced_analyzer.py`)
- Consider running during off-peak hours
- Monitor your API quotas

## 📁 File Structure

```
📦 YouTube Playlist Analyzer
├── 📄 README.md                    # This file
├── 📄 requirements.txt             # Python dependencies
├── 📄 env_example.txt              # Environment variables template
├── 📄 advanced_analyzer.py         # Advanced analyzer (recommended)
├── 📄 project_analysis_*.txt       # Generated results
└── 📄 analysis_progress.json       # Temporary progress file
```

## 🔒 Privacy & Security

- **API Keys**: Keep your `.env` file secure and never commit it to version control
- **Video Content**: Captions are processed locally and sent only to Gemini for analysis
- **No Storage**: The tool doesn't permanently store video content
- **Progress Files**: Automatically cleaned up after successful completion

## 🤝 Tips for Best Results

1. **Ensure good audio quality** in original videos for better auto-captions
2. **Use descriptive video titles** to help with context
3. **Run during off-peak hours** to avoid potential API throttling
4. **Monitor your quotas** in respective API consoles
5. **Check playlist is public** or accessible with your credentials

## 📈 Scaling Up

For larger deployments:
- Consider YouTube Data API v3 paid tiers for higher quotas
- Implement database storage for results
- Add web interface for easier access
- Set up batch processing for multiple playlists

## 🐛 Issues & Support

If you encounter issues:
1. Check your API keys and quotas
2. Verify playlist accessibility
3. Look at error messages for specific guidance
4. Try the basic analyzer if advanced version fails

---

**Ready to analyze your student projects? Start with the advanced analyzer for the best experience!**

```bash
python advanced_analyzer.py
``` 
