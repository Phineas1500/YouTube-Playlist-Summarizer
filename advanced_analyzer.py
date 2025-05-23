#!/usr/bin/env python3
"""
Advanced YouTube Playlist Project Analyzer

Enhanced version with better rate limiting, content chunking for large datasets,
and improved error handling.
"""

import os
import time
import re
import json
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import threading
from queue import Queue

import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from tqdm import tqdm

# OAuth specific imports
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Load environment variables
load_dotenv()

# OAuth 2.0 scopes for YouTube
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

class RateLimiter:
    """Simple rate limiter for API calls."""
    def __init__(self, max_calls_per_minute: int = 1000):
        self.max_calls = max_calls_per_minute
        self.calls = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.calls = [call_time for call_time in self.calls if now - call_time < 60]
            
            if len(self.calls) >= self.max_calls:
                sleep_time = 60 - (now - self.calls[0]) + 1
                if sleep_time > 0:
                    print(f"⏱️  Rate limit reached, waiting {sleep_time:.1f} seconds...")
                    time.sleep(sleep_time)
                    # Reset calls after waiting
                    self.calls = [c for c in self.calls if time.time() - c < 60] 
            
            self.calls.append(now)

class AdvancedYouTubeAnalyzer:
    def __init__(self):
        # self.youtube_api_key = os.getenv('YOUTUBE_API_KEY') # No longer needed for YouTube
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # if not self.youtube_api_key: # No longer needed
        #     raise ValueError("YOUTUBE_API_KEY not found in environment variables")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize YouTube API client with OAuth
        self.youtube = self.get_authenticated_service()
        
        # Initialize Gemini
        genai.configure(api_key=self.gemini_api_key)
        # Ensure you are using the correct model name as per your previous setup
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20') 
        
        # Rate limiters
        # YouTube rate limiting is less critical with OAuth usually, but good to keep
        self.youtube_rate_limiter = RateLimiter(100) 
        self.gemini_rate_limiter = RateLimiter(1000)  # User's Gemini limit
        
        # Cache for captions to avoid re-downloading
        self.caption_cache = {}
        
    def get_authenticated_service(self):
        """Get authenticated YouTube service using OAuth."""
        creds = None
        
        # Check if token.pickle exists (saved credentials)
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials are not valid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("🔐 OAuth authentication required for YouTube API...")
                print("This may open a browser window for authentication if token.pickle is missing or invalid.")
                print("Ensure 'credentials.json' (OAuth 2.0 Client ID for Desktop app) is in the same directory.")
                
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "credentials.json not found. Please download your OAuth 2.0 Client ID JSON file from Google Cloud Console and save it as 'credentials.json'."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0) # Uses a random available port
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        return build('youtube', 'v3', credentials=creds)
    
    def extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from YouTube URL."""
        parsed_url = urlparse(url)
        
        if 'list' in parse_qs(parsed_url.query):
            return parse_qs(parsed_url.query)['list'][0]
        else:
            raise ValueError("Invalid YouTube playlist URL")
    
    def get_playlist_videos(self, playlist_id: str) -> List[Dict]:
        """Fetch all videos from a YouTube playlist with rate limiting."""
        videos = []
        next_page_token = None
        
        print("📹 Fetching playlist videos...")
        
        while True:
            try:
                self.youtube_rate_limiter.wait_if_needed()
                
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response['items']:
                    video_info = {
                        'video_id': item['snippet']['resourceId']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'],
                        'published_at': item['snippet']['publishedAt']
                    }
                    videos.append(video_info)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except HttpError as e:
                print(f"❌ Error fetching playlist: {e}")
                break
        
        print(f"✅ Found {len(videos)} videos in playlist")
        return videos
    
    def get_video_captions(self, video_id: str, title: str) -> Optional[str]:
        """Extract English captions from a YouTube video with caching."""
        if video_id in self.caption_cache:
            return self.caption_cache[video_id]
        
        try:
            self.youtube_rate_limiter.wait_if_needed()
            
            # Get available caption tracks
            captions_request = self.youtube.captions().list(
                part='snippet',
                videoId=video_id
            )
            captions_response = captions_request.execute()
            
            # Look for English captions (prefer auto-generated)
            english_caption_id = None
            backup_caption_id = None
            
            for caption in captions_response['items']:
                snippet = caption['snippet']
                if snippet['language'] == 'en':
                    if snippet['trackKind'] == 'asr':  # Auto speech recognition
                        english_caption_id = caption['id']
                        break
                    elif not backup_caption_id: # Prefer 'asr' but take any 'en' if 'asr' not found
                        backup_caption_id = caption['id']
            
            # Use backup if no auto-generated found
            if not english_caption_id:
                english_caption_id = backup_caption_id
            
            if not english_caption_id:
                print(f"⚠️ No English captions found for '{title}' (Video ID: {video_id}). Available tracks: {len(captions_response['items'])}")
                return None
            
            # Download the caption content
            self.youtube_rate_limiter.wait_if_needed()
            caption_download_request = self.youtube.captions().download(
                id=english_caption_id,
                tfmt='vtt'
            )
            # Note: .execute() for download might return bytes directly, not a JSON response object
            # so we handle it carefully.
            caption_content_bytes = caption_download_request.execute() 
            
            # Clean up the VTT format
            caption_text = self.clean_vtt_content(caption_content_bytes.decode('utf-8'))
            
            # Cache the result
            self.caption_cache[video_id] = caption_text
            return caption_text
            
        except HttpError as e:
            error_details_str = ""
            try:
                # e.content is usually bytes, try to decode to string
                error_content_decoded = e.content.decode('utf-8')
                error_details_str = f"Raw Error Content: {error_content_decoded}"
            except Exception:
                error_details_str = f"Raw Error Content (bytes): {e.content}"

            print(f"⚠️ Error getting captions for '{title}' (Video ID: {video_id}): HTTP {e.resp.status}")
            print(f"   Reason: {e.resp.reason}")
            print(f"   Request URI: {e.uri}")
            if hasattr(e, 'error_details') and e.error_details:
                 print(f"   Error Details (parsed): {e.error_details}")
            print(f"   {error_details_str}")

            if e.resp.status == 403:
                print(f"   🔴 Specific 403 Forbidden error for '{title}'. This is unusual if you own the video and OAuth is correct.")
                print(f"      Is it possible this specific video (ID: {video_id}) has different privacy/sharing settings or was uploaded differently?")
            elif e.resp.status == 404:
                 print(f"   🟡 Specific 404 Not Found for '{title}'. The captions().list might have found a track ID, but download failed.")
                 print(f"      This could mean the caption track exists in metadata but is not downloadable, or video ID was not found for download (less likely here).")

            return None
        except Exception as e:
            # Catch any other unexpected errors
            print(f"⚠️ Unexpected error getting captions for '{title}' (Video ID: {video_id}): {type(e).__name__} - {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None
    
    def clean_vtt_content(self, vtt_content: str) -> str:
        """Clean VTT caption content to extract just the spoken text."""
        lines = vtt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip VTT headers, timestamps, and empty lines
            if (line and 
                not line.startswith('WEBVTT') and 
                not line.startswith('NOTE') and 
                not '-->' in line and 
                not line.isdigit() and
                not re.match(r'^\d{2}:\d{2}:\d{2}', line)):
                
                # Remove HTML tags and special characters
                cleaned_line = re.sub(r'<[^>]+>', '', line)
                cleaned_line = re.sub(r'&[a-zA-Z]+;', ' ', cleaned_line)
                if cleaned_line.strip():
                    text_lines.append(cleaned_line.strip())
        
        return ' '.join(text_lines)
    
    def chunk_content(self, content: str, max_chunk_size: int = 30000) -> List[str]:
        """Split large content into smaller chunks for processing."""
        if len(content) <= max_chunk_size:
            return [content]
        
        chunks = []
        words = content.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def analyze_chunk_with_gemini(self, chunk: str, video_titles: List[str], chunk_num: int, total_chunks: int) -> str:
        """Analyze a single chunk of content with Gemini."""
        prompt = f"""
        You are analyzing student project presentations from a club. This is chunk {chunk_num} of {total_chunks} from transcribed captions of ~60 videos where students present their projects.

        Your task for this chunk:
        1. Identify all student projects mentioned in this text
        2. For each project found, extract:
           - Project name/title
           - Brief description
           - Technologies/tools mentioned
           - Student name(s) if mentioned
           - Any achievements or results

        Video context (some titles): {', '.join(video_titles[:5])}...

        Content to analyze:
        {chunk}

        Format your response as a structured list. If no clear projects are found in this chunk, respond with "No clear projects identified in this chunk."
        """
        
        try:
            self.gemini_rate_limiter.wait_if_needed()
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Error analyzing chunk {chunk_num}: {e}")
            return f"Error analyzing chunk {chunk_num}: {e}"
    
    def synthesize_results(self, chunk_analyses: List[str]) -> str:
        """Use Gemini to synthesize results from all chunks."""
        combined_analysis = "\n\n".join([f"Chunk {i+1} Analysis:\n{analysis}" for i, analysis in enumerate(chunk_analyses)])
        
        synthesis_prompt = f"""
        You are synthesizing results from analyzing student project presentations. Below are the analyses from multiple chunks of content.

        Your task:
        1. Combine and deduplicate all projects mentioned across chunks
        2. Merge information about the same projects from different chunks
        3. Rank projects by significance (frequency of mention, detail level, etc.)
        4. Create a final comprehensive summary

        Format the final result as:
        - Executive Summary (top 5-10 most significant projects)
        - Detailed Project List (all unique projects found)
        - Technology Trends (most mentioned technologies/tools)
        - Notable Achievements

        Chunk analyses to synthesize:
        {combined_analysis}
        """
        
        try:
            self.gemini_rate_limiter.wait_if_needed()
            print("🔄 Synthesizing final results...")
            response = self.model.generate_content(synthesis_prompt)
            return response.text
        except Exception as e:
            print(f"❌ Error synthesizing results: {e}")
            return f"Error during synthesis: {e}"
    
    def save_progress(self, data: Dict, filename: str = "analysis_progress.json"):
        """Save progress to allow resuming if interrupted."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_progress(self, filename: str = "analysis_progress.json") -> Optional[Dict]:
        """Load previous progress if available."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def analyze_playlist(self, playlist_url: str, resume: bool = True) -> str:
        """Main method to analyze a YouTube playlist with resume capability."""
        try:
            # Extract playlist ID
            playlist_id = self.extract_playlist_id(playlist_url)
            print(f"📋 Analyzing playlist: {playlist_id}")
            
            # Check for previous progress
            progress_data = None
            if resume:
                progress_data = self.load_progress()
                if progress_data and progress_data.get('playlist_id') == playlist_id:
                    print("📄 Found previous progress, resuming...")
            
            # Get or load videos
            if progress_data and 'videos' in progress_data:
                videos = progress_data['videos']
                print(f"✅ Loaded {len(videos)} videos from progress")
            else:
                videos = self.get_playlist_videos(playlist_id)
                if not videos:
                    return "❌ No videos found in playlist"
            
            # Extract or load captions
            if progress_data and 'captions' in progress_data:
                all_captions = progress_data['captions']
                video_titles = progress_data['video_titles']
                print(f"✅ Loaded captions from progress ({len(all_captions)} successful extractions)")
            else:
                all_captions = []
                video_titles = []
                successful_extractions = 0
                
                print("🎯 Extracting captions from videos...")
                for i, video in enumerate(tqdm(videos, desc="Processing videos")):
                    video_titles.append(video['title'])
                    
                    captions = self.get_video_captions(video['video_id'], video['title'])
                    if captions:
                        all_captions.append(f"\n--- Video: {video['title']} ---\n{captions}")
                        successful_extractions += 1
                    
                    # Save progress every 10 videos
                    if (i + 1) % 10 == 0:
                        progress = {
                            'playlist_id': playlist_id,
                            'videos': videos,
                            'captions': all_captions,
                            'video_titles': video_titles,
                            'timestamp': datetime.now().isoformat()
                        }
                        self.save_progress(progress)
                
                print(f"✅ Successfully extracted captions from {successful_extractions}/{len(videos)} videos")
            
            if not all_captions:
                return "❌ No captions could be extracted from any videos"
            
            # Combine all captions
            combined_captions = '\n'.join(all_captions)
            print(f"📝 Total caption text length: {len(combined_captions):,} characters")
            
            # Process in chunks if content is large
            chunks = self.chunk_content(combined_captions)
            print(f"📦 Processing content in {len(chunks)} chunks...")
            
            chunk_analyses = []
            # Check if progress_data and chunk_analyses exist
            start_chunk_index = 0
            if progress_data and 'chunk_analyses' in progress_data and len(progress_data['chunk_analyses']) < len(chunks) :
                chunk_analyses = progress_data['chunk_analyses']
                start_chunk_index = len(chunk_analyses)
                print(f"Resuming analysis from chunk {start_chunk_index + 1}/{len(chunks)}")

            for i in range(start_chunk_index, len(chunks)):
                chunk = chunks[i]
                # Pass video_titles for context if needed by your prompt
                analysis_text = self.analyze_chunk_with_gemini(chunk, video_titles, i + 1, len(chunks))
                chunk_analyses.append(analysis_text)
                
                # Save progress after each chunk analysis
                if (i + 1) % 1 == 0: # Save after every chunk, or adjust as needed
                    current_progress = {
                        'playlist_id': playlist_id,
                        'videos': videos, # video details
                        'captions': all_captions, # list of caption strings
                        'video_titles': video_titles, # list of video titles
                        'chunk_analyses': chunk_analyses, # list of analyses from chunks
                        'total_chunks': len(chunks),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.save_progress(current_progress)
                time.sleep(1)  # Brief pause between chunks, good for very high RPM APIs
            
            # Synthesize final results
            final_analysis = self.synthesize_results(chunk_analyses)
            
            # Clean up progress file
            try:
                os.remove("analysis_progress.json")
            except FileNotFoundError:
                pass
            
            return final_analysis
            
        except Exception as e:
            return f"❌ Error during analysis: {e}"

def main():
    """Main function to run the advanced analyzer."""
    print("🎓 Advanced YouTube Playlist Project Analyzer")
    print("=" * 60)
    
    try:
        analyzer = AdvancedYouTubeAnalyzer()
        
        # Get playlist URL from user
        playlist_url = input("Enter YouTube playlist URL: ").strip()
        
        if not playlist_url:
            print("❌ Please provide a valid playlist URL")
            return
        
        # Ask about resuming
        resume = input("Resume from previous progress if available? (y/n, default: y): ").strip().lower()
        resume = resume != 'n'
        
        # Analyze the playlist
        print(f"\n🚀 Starting analysis... (Resume: {resume})")
        start_time = time.time()
        
        result = analyzer.analyze_playlist(playlist_url, resume=resume)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Save results with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"project_analysis_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Advanced YouTube Playlist Project Analysis Results\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Playlist URL: {playlist_url}\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Processing Time: {duration/60:.1f} minutes\n\n")
            f.write(result)
        
        print(f"\n✅ Analysis complete! ({duration/60:.1f} minutes)")
        print(f"📄 Results saved to {output_file}")
        print("\n" + "=" * 60)
        print("ANALYSIS RESULTS:")
        print("=" * 60)
        print(result)
        
    except Exception as e:
        print(f"❌ Application error: {e}")

if __name__ == "__main__":
    main() 