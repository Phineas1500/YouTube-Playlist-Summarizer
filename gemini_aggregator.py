#!/usr/bin/env python3
"""
Gemini Aggregator for analyzing multiple video transcripts
Uses Gemini 2.0 Flash to analyze transcripts and identify student projects
"""

import sys
import json
import os
import traceback
import time
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_playlist_with_gemini(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate and analyze multiple video transcripts using Gemini
    """
    try:
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize Gemini
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        transcripts = data.get('transcripts', '')
        summaries = data.get('summaries', '')
        key_points = data.get('keyPoints', [])
        video_count = data.get('videoCount', 0)
        video_titles = data.get('videoTitles', [])
        
        sys.stderr.write(f"Analyzing {video_count} videos with Gemini\n")
        sys.stderr.write(f"Total transcript length: {len(transcripts)} characters\n")
        sys.stderr.write(f"Total key points: {len(key_points)}\n")
        
        # Create comprehensive analysis prompt
        prompt = f"""
You are analyzing student project presentations from a technical club or class. Below are transcripts from {video_count} videos where students present their projects.

VIDEO TITLES (for context):
{chr(10).join([f"{i+1}. {title}" for i, title in enumerate(video_titles)])}

INDIVIDUAL VIDEO SUMMARIES:
{summaries}

YOUR TASK:
1. **Identify all unique student projects** mentioned across all videos
2. **For each project, extract:**
   - Project name/title
   - Brief description of what the project does
   - Key technologies, tools, or programming languages used
   - Student name(s) if mentioned
   - Notable achievements, results, or impact
   - Level of complexity (beginner/intermediate/advanced)

3. **Categorize projects by type** (e.g., web apps, mobile apps, AI/ML, hardware, games, etc.)

4. **Provide overall insights:**
   - Most popular technologies/frameworks used
   - Common project themes or patterns
   - Skill progression visible across projects
   - Notable innovations or creative solutions

5. **Rank projects** by significance, innovation, or complexity

**IMPORTANT: Your response must be valid JSON format only. Do not include any text before or after the JSON. Start directly with {{ and end with }}.**

Please format your response as a structured JSON with the following format:
{{
  "projects": [
    {{
      "name": "Project Name",
      "description": "What the project does",
      "technologies": ["tech1", "tech2"],
      "students": ["student1", "student2"],
      "category": "project category",
      "complexity": "beginner|intermediate|advanced",
      "achievements": "Notable results or impact",
      "video_source": "Video title where primarily mentioned"
    }}
  ],
  "categories": {{
    "category_name": {{
      "count": 5,
      "projects": ["project1", "project2"]
    }}
  }},
  "technology_trends": {{
    "most_used": ["React", "Python", "JavaScript"],
    "emerging": ["technology emerging"],
    "frameworks": ["popular frameworks"]
  }},
  "insights": {{
    "total_projects": 25,
    "skill_levels": {{"beginner": 10, "intermediate": 12, "advanced": 3}},
    "common_themes": ["theme1", "theme2"],
    "innovations": ["notable innovation1", "innovation2"]
  }},
  "summary": "Overall analysis summary of the entire playlist"
}}

FULL TRANSCRIPTS:
{transcripts}
"""

        # Call Gemini with rate limiting considerations
        sys.stderr.write("Calling Gemini for aggregated analysis...\n")
        
        try:
            # Add a small delay to respect rate limits
            time.sleep(1)
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=8000
                )
            )
            
            sys.stderr.write("Gemini analysis completed\n")
            
            # Parse the JSON response
            try:
                response_text = response.text.strip()
                
                # Handle JSON wrapped in markdown code blocks
                if response_text.startswith('```json'):
                    # Extract JSON from markdown code block
                    lines = response_text.split('\n')
                    json_lines = []
                    in_json = False
                    
                    for line in lines:
                        if line.strip() == '```json':
                            in_json = True
                            continue
                        elif line.strip() == '```' and in_json:
                            break
                        elif in_json:
                            json_lines.append(line)
                    
                    response_text = '\n'.join(json_lines)
                
                analysis_result = json.loads(response_text)
            except json.JSONDecodeError as e:
                sys.stderr.write(f"Failed to parse Gemini JSON response: {e}\n")
                sys.stderr.write(f"Raw response: {response.text[:500]}...\n")
                # Fallback to text analysis
                analysis_result = {
                    "projects": [],
                    "categories": {},
                    "technology_trends": {"most_used": [], "emerging": [], "frameworks": []},
                    "insights": {
                        "total_projects": 0,
                        "skill_levels": {"beginner": 0, "intermediate": 0, "advanced": 0},
                        "common_themes": [],
                        "innovations": []
                    },
                    "summary": response.text,
                    "analysis_type": "text_fallback"
                }
            
            # Validate and enhance the result
            if not isinstance(analysis_result.get('projects'), list):
                analysis_result['projects'] = []
            
            if not isinstance(analysis_result.get('categories'), dict):
                analysis_result['categories'] = {}
            
            # Add metadata
            analysis_result['metadata'] = {
                'video_count': video_count,
                'total_transcript_length': len(transcripts),
                'processing_timestamp': time.time(),
                'model_used': 'gemini-2.0-flash-exp'
            }
            
            return {
                "status": "success",
                "analysis": analysis_result,
                "projects": analysis_result.get('projects', []),
                "avgProcessingTime": time.time()  # Simple timestamp for now
            }
            
        except Exception as gemini_error:
            sys.stderr.write(f"Gemini API error: {str(gemini_error)}\n")
            
            # Fallback analysis using simple text processing
            sys.stderr.write("Attempting fallback analysis...\n")
            fallback_result = create_fallback_analysis(transcripts, video_titles, video_count)
            
            return {
                "status": "success",
                "analysis": fallback_result,
                "projects": fallback_result.get('projects', []),
                "avgProcessingTime": time.time(),
                "note": "Used fallback analysis due to Gemini API error"
            }
        
    except Exception as e:
        sys.stderr.write(f"Error in Gemini analysis: {str(e)}\n")
        sys.stderr.write(traceback.format_exc())
        
        # Return a basic fallback
        return {
            "status": "error",
            "error": str(e),
            "analysis": create_basic_fallback(data),
            "projects": [],
            "avgProcessingTime": 0
        }

def create_fallback_analysis(transcripts: str, video_titles: List[str], video_count: int) -> Dict[str, Any]:
    """
    Create a basic analysis when Gemini is not available
    """
    # Simple keyword-based project detection
    project_keywords = ['project', 'app', 'website', 'game', 'application', 'system', 'tool']
    tech_keywords = ['python', 'javascript', 'react', 'node', 'java', 'c++', 'html', 'css', 'sql', 'mongodb']
    
    # Count technology mentions
    tech_counts = {}
    for tech in tech_keywords:
        count = transcripts.lower().count(tech.lower())
        if count > 0:
            tech_counts[tech] = count
    
    # Sort by frequency
    most_used_tech = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "projects": [
            {
                "name": f"Project from {title[:50]}...",
                "description": "Project detected in video transcript",
                "technologies": [tech[0] for tech in most_used_tech[:3]],
                "students": [],
                "category": "general",
                "complexity": "unknown",
                "achievements": "Details available in transcript",
                "video_source": title
            }
            for title in video_titles[:10]  # Limit to first 10 videos
        ],
        "categories": {
            "general": {
                "count": min(len(video_titles), 10),
                "projects": [f"Project from {title[:30]}..." for title in video_titles[:10]]
            }
        },
        "technology_trends": {
            "most_used": [tech[0] for tech in most_used_tech[:5]],
            "emerging": [],
            "frameworks": []
        },
        "insights": {
            "total_projects": min(len(video_titles), 10),
            "skill_levels": {"beginner": 0, "intermediate": 0, "advanced": 0},
            "common_themes": ["student presentations"],
            "innovations": []
        },
        "summary": f"Basic analysis of {video_count} videos. Technologies mentioned: {', '.join([tech[0] for tech in most_used_tech[:3]])}. Full analysis requires Gemini API access.",
        "analysis_type": "basic_fallback"
    }

def create_basic_fallback(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create minimal analysis when everything fails
    """
    video_count = data.get('videoCount', 0)
    return {
        "projects": [],
        "categories": {},
        "technology_trends": {"most_used": [], "emerging": [], "frameworks": []},
        "insights": {
            "total_projects": 0,
            "skill_levels": {"beginner": 0, "intermediate": 0, "advanced": 0},
            "common_themes": [],
            "innovations": []
        },
        "summary": f"Analysis of {video_count} videos could not be completed due to errors.",
        "analysis_type": "error_fallback"
    }

def main():
    """
    Main function to handle command line input
    """
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python gemini_aggregator.py '<json_data>'\n")
        print(json.dumps({
            "status": "error",
            "error": "Insufficient arguments. Provide JSON data as argument."
        }))
        sys.exit(1)
    
    try:
        # Parse input JSON data
        json_input = sys.argv[1]
        data = json.loads(json_input)
        
        # Process the data
        result = analyze_playlist_with_gemini(data)
        
        # Output result as JSON
        print(json.dumps(result, ensure_ascii=False))
        sys.stdout.flush()
        
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Invalid JSON input: {e}\n")
        print(json.dumps({
            "status": "error",
            "error": f"Invalid JSON input: {e}"
        }))
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        sys.stderr.write(traceback.format_exc())
        print(json.dumps({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }))
        sys.exit(1)

if __name__ == "__main__":
    main() 