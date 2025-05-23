#!/usr/bin/env python3
"""
Modal App for YouTube Playlist Processor
Separate Modal application for Whisper transcription processing
"""

import modal
import os
import io
import json
import tempfile
from pathlib import Path

# Create a new Modal app specifically for playlist processing
app = modal.App("youtube-playlist-processor")

# Create the Whisper image with dependencies
whisper_image = modal.Image.debian_slim(python_version="3.11").apt_install([
    "ffmpeg",  # Install actual ffmpeg binary
    "libsndfile1",  # Audio file support
]).pip_install([
    "openai-whisper",
    "torch",
    "torchaudio", 
    "ffmpeg-python",
    "numpy",
    "scipy"
])

@app.function(
    image=whisper_image,
    gpu="T4",  # Use T4 GPU for cost efficiency
    timeout=3600,  # 1 hour timeout for long videos
    memory=8192,   # 8GB memory
)
def process_audio(audio_data: bytes, filename: str) -> dict:
    """
    Process audio data through Whisper and return transcription with analysis
    
    Args:
        audio_data: Raw audio file bytes
        filename: Original filename for context
    
    Returns:
        dict: Processing results including transcript, summary, etc.
    """
    import whisper
    import tempfile
    import os
    import json
    from pathlib import Path
    
    try:
        print(f"Processing audio for: {filename}")
        print(f"Audio data size: {len(audio_data)} bytes")
        
        # Load Whisper model (using base model for balance of speed/accuracy)
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        
        # Create temporary file for audio data
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name
        
        try:
            print(f"Starting transcription...")
            
            # Transcribe the audio
            result = model.transcribe(
                temp_audio_path,
                language="en",  # Assuming English, can be made configurable
                task="transcribe",
                verbose=False
            )
            
            transcript = result["text"].strip()
            segments = result.get("segments", [])
            
            print(f"Transcription completed. Length: {len(transcript)} characters")
            
            # Generate summary and key points (simple extraction for now)
            summary = generate_simple_summary(transcript, filename)
            key_points = extract_key_points(transcript)
            flashcards = generate_flashcards(transcript)
            
            # Format segments for frontend
            formatted_segments = []
            for segment in segments[:10]:  # Limit to first 10 segments
                formatted_segments.append({
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                    "text": segment.get("text", "").strip()
                })
            
            # Calculate basic stats
            stats = {
                "transcript_length": len(transcript),
                "word_count": len(transcript.split()),
                "segments_count": len(segments),
                "duration": segments[-1].get("end", 0) if segments else 0
            }
            
            result_data = {
                "status": "success",
                "transcript": transcript,
                "summary": summary,
                "keyPoints": key_points,
                "flashcards": flashcards,
                "segments": formatted_segments,
                "stats": stats,
                "filename": filename
            }
            
            print(f"Processing completed successfully for {filename}")
            return result_data
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_audio_path)
            except:
                pass
                
    except Exception as e:
        print(f"Error processing {filename}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": "error",
            "error": str(e),
            "filename": filename,
            "transcript": "",
            "summary": f"Error processing {filename}: {str(e)}",
            "keyPoints": [],
            "flashcards": [],
            "segments": [],
            "stats": {}
        }

def generate_simple_summary(transcript: str, filename: str) -> str:
    """
    Generate a simple summary of the transcript
    """
    if not transcript or len(transcript) < 100:
        return f"Short transcript from {filename}"
    
    # Simple extractive summary - take first few sentences and key phrases
    sentences = transcript.split('. ')
    
    # Take first 2-3 sentences as summary
    summary_sentences = sentences[:min(3, len(sentences))]
    summary = '. '.join(summary_sentences)
    
    if len(summary) > 500:
        summary = summary[:500] + "..."
    
    return summary

def extract_key_points(transcript: str) -> list:
    """
    Extract key points from transcript using simple keyword matching
    """
    if not transcript:
        return []
    
    key_points = []
    
    # Look for common presentation indicators
    indicators = [
        "project", "built", "created", "developed", "implemented",
        "technology", "framework", "language", "tool", "library",
        "problem", "solution", "challenge", "goal", "objective",
        "result", "outcome", "achievement", "learned", "improved"
    ]
    
    sentences = transcript.split('. ')
    
    for sentence in sentences[:20]:  # Limit to first 20 sentences
        sentence_lower = sentence.lower()
        for indicator in indicators:
            if indicator in sentence_lower and len(sentence.strip()) > 20:
                key_points.append(sentence.strip())
                break
    
    # Remove duplicates and limit to 10 points
    unique_points = list(dict.fromkeys(key_points))[:10]
    return unique_points

def generate_flashcards(transcript: str) -> list:
    """
    Generate simple flashcards from transcript
    """
    if not transcript or len(transcript) < 100:
        return []
    
    flashcards = []
    
    # Look for definition-like patterns
    sentences = transcript.split('. ')
    
    for sentence in sentences[:10]:  # Limit processing
        if any(word in sentence.lower() for word in ['is', 'means', 'refers to', 'defined as']):
            # Try to extract question/answer pairs
            if len(sentence) > 30 and len(sentence) < 200:
                # Simple heuristic for flashcard creation
                parts = sentence.split(' is ')
                if len(parts) == 2:
                    flashcards.append({
                        "question": f"What is {parts[0].strip()}?",
                        "answer": parts[1].strip()
                    })
    
    return flashcards[:5]  # Limit to 5 flashcards

# Serve the Modal app locally for testing
@app.local_entrypoint()
def main():
    """
    Local entrypoint for testing the Modal app
    """
    print("YouTube Playlist Processor Modal App")
    print("Available functions:")
    print("- process_audio: Process audio data through Whisper")
    print("\nTo test, call: modal run modal_app.py")

if __name__ == "__main__":
    main() 