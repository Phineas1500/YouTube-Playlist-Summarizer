#!/usr/bin/env python3
"""
Modal Processor for individual video audio files
Processes audio through Modal's Whisper service and returns transcription with analysis
"""

import sys
import json
import os
import traceback
from pathlib import Path
from modal import Function

def process_single_video_audio(audio_path, filename):
    """
    Process a single audio file through Modal's Whisper service
    """
    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        audio_size = os.path.getsize(audio_path)
        sys.stderr.write(f"Processing audio file: {audio_path} ({audio_size} bytes)\n")
        
        # Read audio data
        with open(audio_path, 'rb') as audio_file:
            audio_data = audio_file.read()
        
        sys.stderr.write(f"Read {len(audio_data)} bytes of audio data\n")
        
        # Connect to our dedicated Modal app using Function.lookup
        sys.stderr.write("Connecting to Modal service...\n")
        
        try:
            # Use Function.lookup to get the specific function from our app
            process_audio_fn = Function.lookup("youtube-playlist-processor", "process_audio")
            
        except Exception as lookup_error:
            sys.stderr.write(f"Failed to lookup Modal function: {lookup_error}\n")
            sys.stderr.write("Make sure the Modal app is deployed. Run: modal deploy modal_app.py\n")
            raise Exception(f"Modal function lookup failed: {lookup_error}")
        
        # Call Modal function (blocking)
        sys.stderr.write(f"Calling Modal function for: {filename}...\n")
        result = process_audio_fn.remote(audio_data, filename)
        sys.stderr.write("Modal function call completed.\n")
        
        # Validate result
        if result is None:
            raise Exception("Did not receive a result from Modal function.")
        
        if not isinstance(result, dict):
            raise Exception(f"Expected dict result, got: {type(result)}")
            
        if result.get("status") == "error":
            error_detail = result.get('error', 'Unknown error')
            raise Exception(f"Modal function failed: {error_detail}")
        
        # The result should already be in the right format from our Modal app
        sys.stderr.write(f"Processing completed successfully for {filename}\n")
        print(json.dumps(result, ensure_ascii=False))
        sys.stdout.flush()
        
    except Exception as e:
        sys.stderr.write(f"Error processing {filename}: {str(e)}\n")
        sys.stderr.write(traceback.format_exc())
        
        error_output = {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "transcript": "",
            "summary": f"Error processing {filename}: {str(e)}",
            "keyPoints": [],
            "flashcards": [],
            "segments": [],
            "stats": {}
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.stdout.flush()

def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: python modal_processor.py <audio_path> <filename>\n")
        print(json.dumps({
            "status": "error",
            "error": "Insufficient arguments. Usage: python modal_processor.py <audio_path> <filename>"
        }))
        sys.exit(1)
    
    audio_path = sys.argv[1]
    filename = sys.argv[2]
    
    process_single_video_audio(audio_path, filename)

if __name__ == "__main__":
    main() 