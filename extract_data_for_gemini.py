#!/usr/bin/env python3
"""
Extract completed transcript data for Gemini analysis
"""

import json
import sys

def extract_data_for_gemini(job_file):
    """Extract and format data from completed job for Gemini analysis"""
    
    with open(job_file, 'r') as f:
        job_data = json.load(f)
    
    # Extract the video data
    videos = job_data['data']['individualVideos']
    
    # Combine all transcripts and data
    all_transcripts = ''
    all_summaries = ''
    key_points = []
    video_titles = []
    
    for video in videos:
        title = video.get('title', 'Unknown Title')
        video_titles.append(title)
        
        if 'data' in video and video['data']:
            transcript = video['data'].get('transcript', '')
            summary = video['data'].get('summary', '')
            
            all_transcripts += f'\n\n=== {title} ===\n{transcript}'
            all_summaries += f'\n\n=== {title} ===\n{summary}'
            
            if 'keyPoints' in video['data']:
                key_points.extend(video['data']['keyPoints'])
    
    # Create the input data for Gemini
    gemini_input = {
        'transcripts': all_transcripts,
        'summaries': all_summaries,
        'keyPoints': key_points,
        'videoCount': len(videos),
        'videoTitles': video_titles
    }
    
    return gemini_input

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 extract_data_for_gemini.py <job_file.json>")
        sys.exit(1)
    
    job_file = sys.argv[1]
    
    try:
        data = extract_data_for_gemini(job_file)
        print(json.dumps(data))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1) 