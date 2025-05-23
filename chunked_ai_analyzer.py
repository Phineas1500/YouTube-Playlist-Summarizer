#!/usr/bin/env python3
"""
Chunked AI Analyzer - Uses Gemini to analyze transcript chunks for comprehensive project extraction
"""

import json
import re
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import google.generativeai as genai

def load_existing_projects() -> List[str]:
    """Load existing projects from theProjects.md for reference"""
    try:
        with open('theProjects.md', 'r') as f:
            content = f.read()
        
        # Extract project names from the markdown
        project_names = []
        lines = content.split('\n')
        
        for line in lines:
            # Look for numbered project entries like " 1. **Project Name**"
            match = re.match(r'\s*\d+\.\s*\*\*([^*]+)\*\*', line)
            if match:
                project_names.append(match.group(1).strip())
        
        print(f"Loaded {len(project_names)} existing projects for reference")
        return project_names
        
    except FileNotFoundError:
        print("No existing projects file found, starting fresh")
        return []

def create_transcript_chunks(transcripts: str, video_titles: List[str], chunk_size: int = 15000) -> List[Dict]:
    """Split transcripts into manageable chunks for AI analysis"""
    
    # Simple chunking by character count with some overlap
    chunks = []
    overlap = 2000  # Overlap to avoid splitting projects across chunks
    
    start = 0
    chunk_num = 1
    
    while start < len(transcripts):
        end = min(start + chunk_size, len(transcripts))
        
        # Try to end at a sentence boundary
        if end < len(transcripts):
            # Look for sentence ending within last 500 chars
            sentence_end = transcripts.rfind('.', end - 500, end)
            if sentence_end > start + chunk_size // 2:
                end = sentence_end + 1
        
        chunk_text = transcripts[start:end]
        
        chunks.append({
            'chunk_num': chunk_num,
            'text': chunk_text,
            'start_pos': start,
            'end_pos': end,
            'length': len(chunk_text)
        })
        
        start = max(start + chunk_size - overlap, end - overlap)
        chunk_num += 1
    
    print(f"Created {len(chunks)} transcript chunks (avg {chunk_size:,} chars each)")
    return chunks

def analyze_chunk_with_gemini(chunk_text: str, existing_projects: List[str], chunk_num: int, total_chunks: int) -> Dict:
    """Analyze a single chunk with Gemini"""
    
    # Create prompt for this specific chunk
    prompt = f"""
You are analyzing student project presentations from Purdue Hackers. This is chunk {chunk_num} of {total_chunks}.

EXISTING PROJECTS (for reference to avoid duplicates):
{chr(10).join(f"- {name}" for name in existing_projects[:20])}  # Show first 20 for context

Your task: Find ALL student projects mentioned in this transcript chunk, including:
- Personal coding projects (any complexity level)
- Technical experiments and prototypes  
- Hardware builds and hacks
- Creative projects involving technology
- Course projects with technical components
- Research projects and algorithms
- Infrastructure and system administration work
- Any technical learning projects or tutorials followed

Be INCLUSIVE - capture projects of all sizes and complexity levels.

Return ONLY valid JSON in this exact format:
{{
  "projects": [
    {{
      "name": "Project Name",
      "description": "Detailed description from transcript",
      "technologies": ["Tech1", "Tech2"],
      "status": "completed|in-progress|planned", 
      "features": "Key features and functionality",
      "category": "Web App|Mobile App|Hardware|Game|Tool|Research|Infrastructure|Other",
      "complexity": "beginner|intermediate|advanced",
      "notes": "Additional context from transcript"
    }}
  ]
}}

TRANSCRIPT CHUNK:
{chunk_text}
"""

    try:
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print(f"Analyzing chunk {chunk_num}/{total_chunks} ({len(chunk_text):,} chars)...")
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=8192,
                temperature=0.3,
            )
        )
        
        try:
            # Use robust parsing function
            projects = parse_chunk_response(response.text)
            print(f"✅ Chunk {chunk_num}: Found {len(projects)} projects")
            
            return {
                'projects': projects,
                'chunk_summary': f'Projects extracted from chunk {chunk_num}',
                'extraction_confidence': 'high',
                'chunk_info': {
                    'chunk_num': chunk_num,
                    'total_chunks': total_chunks,
                    'chunk_length': len(chunk_text)
                }
            }
            
        except Exception as e:
            print(f"❌ Error processing chunk {chunk_num}: {e}")
            return {
                'projects': [],
                'chunk_summary': f'Error processing chunk {chunk_num}',
                'extraction_confidence': 'low',
                'error': str(e)
            }
            
    except Exception as e:
        print(f"❌ Error with Gemini API for chunk {chunk_num}: {e}")
        return {
            'projects': [],
            'chunk_summary': f'API error for chunk {chunk_num}',
            'extraction_confidence': 'low',
            'error': str(e)
        }

def parse_chunk_response(response_text: str) -> List[Dict]:
    """Parse Gemini response with robust error handling"""
    try:
        # Clean up the response text first
        cleaned_text = response_text.strip()
        
        # Remove code block markers if present
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]  # Remove ```json
        elif cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]   # Remove ```
            
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            
        cleaned_text = cleaned_text.strip()
        
        # Try to parse the cleaned JSON
        data = json.loads(cleaned_text)
        return data.get('projects', [])
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Raw response: \n{response_text[:500]}...")
        
        # Try to extract projects using regex as fallback
        projects = []
        try:
            # Look for the projects array specifically
            projects_pattern = r'"projects"\s*:\s*\[(.*?)\]'
            projects_match = re.search(projects_pattern, response_text, re.DOTALL)
            
            if projects_match:
                projects_content = projects_match.group(1)
                
                # Split by project objects and parse each one
                project_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', projects_content)
                
                for project_str in project_objects:
                    try:
                        # Clean up the project string
                        project_str = project_str.strip().rstrip(',')
                        project = json.loads(project_str)
                        if 'name' in project:
                            projects.append(project)
                    except:
                        continue
                        
            print(f"✅ Recovered {len(projects)} projects from malformed JSON")
            return projects
            
        except Exception as fallback_error:
            print(f"❌ Fallback parsing also failed: {fallback_error}")
            return []

def are_projects_similar(proj1: Dict, proj2: Dict) -> bool:
    """Check if two projects are similar enough to be considered duplicates"""
    name1 = proj1.get('name', '').lower().strip()
    name2 = proj2.get('name', '').lower().strip()
    
    # Exact name match (case insensitive)
    if name1 == name2:
        return True
    
    # Very high similarity threshold for fuzzy matching
    from difflib import SequenceMatcher
    similarity = SequenceMatcher(None, name1, name2).ratio()
    
    # Only consider duplicates if:
    # 1. Names are very similar (>0.9 similarity) AND
    # 2. Names are reasonably long (>10 chars to avoid false positives) AND  
    # 3. Description similarity is also high
    if similarity > 0.9 and len(name1) > 10 and len(name2) > 10:
        desc1 = proj1.get('description', '').lower()
        desc2 = proj2.get('description', '').lower()
        desc_similarity = SequenceMatcher(None, desc1, desc2).ratio()
        
        # Require both name and description to be very similar
        if desc_similarity > 0.8:
            return True
    
    return False

def deduplicate_projects(projects: List[Dict]) -> List[Dict]:
    """Remove duplicate projects with conservative matching"""
    unique_projects = []
    duplicates_found = 0
    
    for project in projects:
        is_duplicate = False
        for existing in unique_projects:
            if are_projects_similar(project, existing):
                print(f"Potential duplicate: '{project.get('name', 'Unknown')}' similar to '{existing.get('name', 'Unknown')}'")
                is_duplicate = True
                duplicates_found += 1
                break
        
        if not is_duplicate:
            unique_projects.append(project)
    
    print(f"Deduplication: {len(projects)} → {len(unique_projects)} projects ({duplicates_found} duplicates removed)")
    return unique_projects

def main():
    """Main function"""
    
    try:
        # Load transcript data
        with open('gemini_input.json', 'r') as f:
            data = json.load(f)
        
        transcripts = data.get('transcripts', '')
        video_titles = data.get('videoTitles', [])
        video_count = data.get('videoCount', 0)
        
        print(f"🎯 Starting chunked AI analysis of {video_count} videos")
        print(f"📊 Total transcript length: {len(transcripts):,} characters")
        
        # Load existing projects for reference
        existing_projects = load_existing_projects()
        
        # Create transcript chunks
        chunks = create_transcript_chunks(transcripts, video_titles, chunk_size=15000)
        
        # Analyze each chunk with Gemini
        all_results = []
        all_projects = []
        
        for i, chunk in enumerate(chunks, 1):
            print(f"Analyzing chunk {i}/{len(chunks)} ({len(chunk):,} chars)...")
            
            result = analyze_chunk_with_gemini(chunk['text'], existing_projects, i, len(chunks))
            all_results.append(result)
            
            # Collect projects from this chunk
            chunk_projects = result.get('projects', [])
            for project in chunk_projects:
                # Add chunk info to each project
                project['source_chunk'] = i
                project['analysis_method'] = 'chunked_ai'
                all_projects.append(project)
        
        print(f"\n✅ Completed analysis of {len(chunks)} chunks")
        print(f"📊 Total projects found: {len(all_projects)}")
        
        # Deduplicate projects
        unique_projects = deduplicate_projects(all_projects)
        
        # Create categories and summaries
        categories = {}
        tech_count = {}
        status_count = {}
        complexity_count = {}
        
        for project in unique_projects:
            # Categories
            cat = project.get('category', 'Other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(project['name'])
            
            # Technologies
            for tech in project.get('technologies', []):
                tech_count[tech] = tech_count.get(tech, 0) + 1
            
            # Status
            status = project.get('status', 'unknown')
            status_count[status] = status_count.get(status, 0) + 1
            
            # Complexity
            complexity = project.get('complexity', 'unknown')
            complexity_count[complexity] = complexity_count.get(complexity, 0) + 1
        
        # Create final result
        final_result = {
            'status': 'success',
            'analysis': {
                'projects': unique_projects,
                'categories': {cat: {'count': len(projs), 'projects': projs} for cat, projs in categories.items()},
                'technology_summary': {'languages': tech_count},
                'status_summary': status_count,
                'complexity_summary': complexity_count,
                'chunk_results': all_results,
                'insights': {
                    'total_projects': len(unique_projects),
                    'total_chunks_analyzed': len(chunks),
                    'projects_before_dedup': len(all_projects),
                    'most_common_category': max(categories.keys(), key=lambda x: len(categories[x])) if categories else 'None',
                    'most_used_technology': max(tech_count.keys(), key=lambda x: tech_count[x]) if tech_count else 'None'
                },
                'metadata': {
                    'video_count': video_count,
                    'total_transcript_length': len(transcripts),
                    'analysis_method': 'chunked_ai_gemini',
                    'chunk_size': 15000,
                    'total_chunks': len(chunks),
                    'existing_projects_referenced': len(existing_projects)
                }
            },
            'projects': unique_projects
        }
        
        # Save results
        with open('chunked_ai_results.json', 'w') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 CHUNKED AI ANALYSIS COMPLETE!")
        print(f"📊 Results:")
        print(f"   • Total unique projects: {len(unique_projects)}")
        print(f"   • Projects before dedup: {len(all_projects)}")
        print(f"   • Chunks analyzed: {len(chunks)}")
        print(f"   • Categories: {len(categories)}")
        print(f"   • Technologies: {len(tech_count)}")
        
        # Show top categories
        print(f"\n📈 Top Categories:")
        for cat, project_list in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            print(f"   • {cat}: {len(project_list)} projects")
        
        # Show top technologies
        print(f"\n🔧 Top Technologies:")
        for tech, count in sorted(tech_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {tech}: {count} projects")
        
        return final_result
        
    except Exception as e:
        print(f"❌ Error in chunked AI analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main() 