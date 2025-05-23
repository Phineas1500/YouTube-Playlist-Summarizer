#!/usr/bin/env python3
"""
Extract and clean the final analysis from Gemini results
"""

import json
import re

def extract_final_analysis():
    """Extract the JSON analysis from Gemini's markdown-wrapped response"""
    
    # Load the results
    with open('gemini_results.json', 'r') as f:
        data = json.load(f)
    
    # Extract the JSON from the summary field
    summary = data['analysis']['summary']
    
    # Find the JSON content between ```json and ```
    json_match = re.search(r'```json\n(.*?)(?:\n```|$)', summary, re.DOTALL)
    if json_match:
        json_content = json_match.group(1)
        
        # Parse the extracted JSON
        try:
            projects_data = json.loads(json_content)
            
            # Save the properly parsed results
            final_result = {
                'status': 'success',
                'analysis': projects_data,
                'projects': projects_data.get('projects', []),
                'metadata': data['analysis']['metadata']
            }
            
            with open('final_analysis.json', 'w') as f:
                json.dump(final_result, f, indent=2)
            
            print(f'✅ Successfully parsed {len(projects_data.get("projects", []))} projects!')
            print(f'📁 Categories found: {list(projects_data.get("categories", {}).keys())}')
            print(f'🔧 Technologies: {", ".join(projects_data.get("technology_trends", {}).get("most_used", [])[:5])}')
            print(f'📊 Total videos analyzed: {data["analysis"]["metadata"]["video_count"]}')
            
            return final_result
            
        except json.JSONDecodeError as e:
            print(f'❌ JSON parsing failed: {e}')
            print('Raw content preview:')
            print(json_content[:500] + '...')
            return None
    else:
        print('❌ No JSON found in summary')
        return None

if __name__ == "__main__":
    extract_final_analysis() 