#!/usr/bin/env python3
"""
Convert chunked AI analysis results to final markdown report
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, List

def format_project_markdown(project: Dict[str, Any], index: int) -> str:
    """Format a single project as markdown"""
    name = project.get('name', 'Unknown Project')
    description = project.get('description', 'No description available')
    technologies = project.get('technologies', [])
    status = project.get('status', 'unknown')
    features = project.get('features', '')
    category = project.get('category', 'Other')
    complexity = project.get('complexity', 'unknown')
    notes = project.get('notes', '')
    source_chunk = project.get('source_chunk', 'unknown')
    
    # Status emoji mapping
    status_emoji = {
        'completed': '✅',
        'published': '🚀',
        'deployed': '🌐',
        'in-progress': '🔄',
        'prototype': '🧪',
        'unknown': '❓'
    }
    
    # Category emoji mapping
    category_emoji = {
        'Web App': '🌐',
        'Mobile App': '📱',
        'AI/ML': '🤖',
        'Hardware': '⚡',
        'Game': '🎮',
        'Tool': '🔧',
        'Library': '📚',
        'Infrastructure': '🏗️',
        'Creative': '🎨',
        'Other': '📦'
    }
    
    # Complexity indicator
    complexity_emoji = {
        'beginner': '🟢',
        'intermediate': '🟡',
        'advanced': '🔴',
        'unknown': '⚪'
    }
    
    markdown = []
    markdown.append(f"## {index}. {name}")
    markdown.append("")
    markdown.append(f"**Category:** {category_emoji.get(category, '📦')} {category}")
    markdown.append(f"**Status:** {status_emoji.get(status, '❓')} {status.title()}")
    markdown.append(f"**Complexity:** {complexity_emoji.get(complexity, '⚪')} {complexity.title()}")
    
    if technologies:
        tech_badges = [f"`{tech}`" for tech in technologies]
        markdown.append(f"**Technologies:** {' '.join(tech_badges)}")
    
    markdown.append("")
    markdown.append("### Description")
    markdown.append(description)
    
    if features and len(features.strip()) > 5:
        markdown.append("")
        markdown.append("### Features & Achievements")
        markdown.append(features)
    
    if notes and len(notes.strip()) > 5:
        markdown.append("")
        markdown.append("### Additional Notes")
        markdown.append(notes)
    
    markdown.append("")
    markdown.append(f"*Found in chunk {source_chunk} via AI analysis*")
    markdown.append("")
    markdown.append("---")
    markdown.append("")
    
    return '\n'.join(markdown)

def create_category_summary(projects: List[Dict[str, Any]]) -> str:
    """Create a category summary section"""
    categories = {}
    for project in projects:
        category = project.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(project.get('name', 'Unknown'))
    
    # Category emoji mapping
    category_emoji = {
        'Web App': '🌐',
        'Mobile App': '📱',
        'AI/ML': '🤖',
        'Hardware': '⚡',
        'Game': '🎮',
        'Tool': '🔧',
        'Library': '📚',
        'Infrastructure': '🏗️',
        'Creative': '🎨',
        'Other': '📦'
    }
    
    markdown = []
    markdown.append("## 📊 Projects by Category")
    markdown.append("")
    
    # Sort categories by count
    sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
    
    for category, project_names in sorted_categories:
        emoji = category_emoji.get(category, '📦')
        markdown.append(f"### {emoji} {category} ({len(project_names)} projects)")
        for name in project_names:
            markdown.append(f"- {name}")
        markdown.append("")
    
    return '\n'.join(markdown)

def create_complexity_summary(projects: List[Dict[str, Any]]) -> str:
    """Create a complexity summary section"""
    complexity_count = {}
    for project in projects:
        complexity = project.get('complexity', 'unknown')
        complexity_count[complexity] = complexity_count.get(complexity, 0) + 1
    
    # Complexity emoji mapping
    complexity_emoji = {
        'beginner': '🟢',
        'intermediate': '🟡',
        'advanced': '🔴',
        'unknown': '⚪'
    }
    
    markdown = []
    markdown.append("## 📊 Projects by Complexity")
    markdown.append("")
    
    # Sort by complexity order
    complexity_order = ['beginner', 'intermediate', 'advanced', 'unknown']
    
    for complexity in complexity_order:
        if complexity in complexity_count:
            count = complexity_count[complexity]
            emoji = complexity_emoji.get(complexity, '⚪')
            markdown.append(f"- {emoji} **{complexity.title()}**: {count} project{'s' if count > 1 else ''}")
    
    markdown.append("")
    return '\n'.join(markdown)

def create_technology_summary(projects: List[Dict[str, Any]]) -> str:
    """Create a technology usage summary"""
    tech_count = {}
    for project in projects:
        for tech in project.get('technologies', []):
            tech_count[tech] = tech_count.get(tech, 0) + 1
    
    if not tech_count:
        return ""
    
    markdown = []
    markdown.append("## 🔧 Technology Usage")
    markdown.append("")
    
    # Sort technologies by usage
    sorted_tech = sorted(tech_count.items(), key=lambda x: x[1], reverse=True)
    
    for tech, count in sorted_tech:
        markdown.append(f"- **{tech}**: {count} project{'s' if count > 1 else ''}")
    
    markdown.append("")
    return '\n'.join(markdown)

def create_chunk_summary(chunk_results: List[Dict]) -> str:
    """Create a summary of chunk analysis results"""
    markdown = []
    markdown.append("## 📝 Analysis Chunk Summary")
    markdown.append("")
    
    total_chunks = len(chunk_results)
    successful_chunks = len([r for r in chunk_results if r.get('extraction_confidence') != 'low'])
    total_projects_raw = sum(len(r.get('projects', [])) for r in chunk_results)
    
    markdown.append(f"- **Total chunks analyzed**: {total_chunks}")
    markdown.append(f"- **Successful extractions**: {successful_chunks}")
    markdown.append(f"- **Projects found (before dedup)**: {total_projects_raw}")
    markdown.append("")
    
    markdown.append("### Chunk Details")
    for i, chunk_result in enumerate(chunk_results, 1):
        projects_in_chunk = len(chunk_result.get('projects', []))
        confidence = chunk_result.get('extraction_confidence', 'unknown')
        summary = chunk_result.get('chunk_summary', 'No summary available')
        
        confidence_emoji = {'high': '🟢', 'medium': '🟡', 'low': '🔴'}.get(confidence, '⚪')
        
        markdown.append(f"**Chunk {i}**: {confidence_emoji} {projects_in_chunk} projects ({confidence} confidence)")
        if summary and len(summary) > 10:
            markdown.append(f"  - {summary}")
        markdown.append("")
    
    return '\n'.join(markdown)

def convert_chunked_results():
    """Main function to convert chunked AI results to markdown"""
    
    try:
        # Load the chunked AI results
        with open('chunked_ai_results.json', 'r') as f:
            data = json.load(f)
        
        # Extract metadata
        metadata = data.get('analysis', {}).get('metadata', {})
        insights = data.get('analysis', {}).get('insights', {})
        
        video_count = metadata.get('video_count', 0)
        transcript_length = metadata.get('total_transcript_length', 0)
        chunk_size = metadata.get('chunk_size', 15000)
        total_chunks = metadata.get('total_chunks', 0)
        existing_projects_count = metadata.get('existing_projects_referenced', 0)
        
        total_projects = insights.get('total_projects', 0)
        projects_before_dedup = insights.get('projects_before_dedup', 0)
        most_common_category = insights.get('most_common_category', 'Unknown')
        most_used_tech = insights.get('most_used_technology', 'Unknown')
        
        # Extract projects and chunk results
        projects = data.get('analysis', {}).get('projects', [])
        chunk_results = data.get('analysis', {}).get('chunk_results', [])
        
        if not projects:
            print("❌ No projects found in the chunked AI results")
            return
        
        print(f"✅ Found {len(projects)} projects from chunked AI analysis")
        
        # Create markdown content
        markdown_content = []
        
        # Header
        markdown_content.append("# 🎓 Purdue Hackers Student Projects - Complete AI Analysis")
        markdown_content.append("")
        markdown_content.append(f"*Comprehensive analysis of {video_count} Checkpoint videos using chunked AI processing*")
        markdown_content.append("")
        markdown_content.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        markdown_content.append(f"**Videos Analyzed:** {video_count}")
        markdown_content.append(f"**Total Transcript Length:** {transcript_length:,} characters")
        markdown_content.append(f"**Projects Found:** {len(projects)}")
        markdown_content.append(f"**Analysis Method:** Chunked AI with Gemini 2.0 Flash")
        markdown_content.append("")
        markdown_content.append("### Analysis Details")
        markdown_content.append(f"- 🧩 **Chunks processed**: {total_chunks} chunks ({chunk_size:,} chars each)")
        markdown_content.append(f"- 🔍 **Projects before deduplication**: {projects_before_dedup}")
        markdown_content.append(f"- 📚 **Existing projects referenced**: {existing_projects_count}")
        markdown_content.append(f"- 📊 **Most common category**: {most_common_category}")
        markdown_content.append(f"- 🔧 **Most used technology**: {most_used_tech}")
        markdown_content.append("")
        markdown_content.append("---")
        markdown_content.append("")
        
        # Table of Contents
        markdown_content.append("## 📑 Table of Contents")
        markdown_content.append("")
        markdown_content.append("- [Projects by Category](#-projects-by-category)")
        markdown_content.append("- [Projects by Complexity](#-projects-by-complexity)")
        markdown_content.append("- [Technology Usage](#-technology-usage)")
        markdown_content.append("- [Analysis Chunk Summary](#-analysis-chunk-summary)")
        markdown_content.append("- [All Projects](#-all-projects)")
        for i, project in enumerate(projects, 1):
            name = project.get('name', 'Unknown Project')
            # Create anchor link
            anchor = name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('.', '').replace('/', '').replace(':', '')
            markdown_content.append(f"  - [{i}. {name}](#{i}-{anchor})")
        markdown_content.append("")
        markdown_content.append("---")
        markdown_content.append("")
        
        # Category summary
        markdown_content.append(create_category_summary(projects))
        markdown_content.append("---")
        markdown_content.append("")
        
        # Complexity summary
        markdown_content.append(create_complexity_summary(projects))
        markdown_content.append("---")
        markdown_content.append("")
        
        # Technology summary
        tech_summary = create_technology_summary(projects)
        if tech_summary:
            markdown_content.append(tech_summary)
            markdown_content.append("---")
            markdown_content.append("")
        
        # Chunk summary
        if chunk_results:
            markdown_content.append(create_chunk_summary(chunk_results))
            markdown_content.append("---")
            markdown_content.append("")
        
        # All projects
        markdown_content.append("## 🚀 All Projects")
        markdown_content.append("")
        markdown_content.append("*Projects identified through AI analysis of transcript chunks, sorted by category and complexity*")
        markdown_content.append("")
        
        for i, project in enumerate(projects, 1):
            markdown_content.append(format_project_markdown(project, i))
        
        # Footer
        markdown_content.append("---")
        markdown_content.append("")
        markdown_content.append("## 📝 Methodology")
        markdown_content.append("")
        markdown_content.append("This analysis used advanced AI techniques to extract student projects:")
        markdown_content.append("")
        markdown_content.append("### 🧩 Chunked Processing")
        markdown_content.append(f"- Split {transcript_length:,} characters into {total_chunks} overlapping chunks")
        markdown_content.append(f"- Each chunk ~{chunk_size:,} characters with 2,000 character overlap")
        markdown_content.append("- Prevents project information from being split across boundaries")
        markdown_content.append("")
        markdown_content.append("### 🤖 AI Analysis")
        markdown_content.append("- Used Google Gemini 2.0 Flash for intelligent project identification")
        markdown_content.append("- Custom prompts designed for technical project extraction")
        markdown_content.append("- Referenced existing projects to avoid duplicates")
        markdown_content.append("- Classified projects by category, status, and complexity")
        markdown_content.append("")
        markdown_content.append("### 🔍 Deduplication")
        markdown_content.append("- Fuzzy matching to identify similar project names")
        markdown_content.append("- Cross-referenced with previously identified projects")
        markdown_content.append(f"- Reduced {projects_before_dedup} raw projects to {len(projects)} unique ones")
        markdown_content.append("")
        markdown_content.append("### 📊 Quality Indicators")
        markdown_content.append("- 🟢 **Beginner**: Simple scripts, first projects, learning exercises")
        markdown_content.append("- 🟡 **Intermediate**: Working applications, deployed projects, API integrations")
        markdown_content.append("- 🔴 **Advanced**: Complex systems, published apps, innovative implementations")
        markdown_content.append("")
        markdown_content.append("---")
        markdown_content.append("")
        markdown_content.append(f"**Final Summary:** {len(projects)} student projects identified across {len(set(p.get('category') for p in projects))} categories using {len(set(tech for p in projects for tech in p.get('technologies', [])))} different technologies from Purdue Hackers Checkpoint video analysis.")
        
        # Write to file
        markdown_text = '\n'.join(markdown_content)
        
        with open('purdue_hackers_chunked_ai_analysis.md', 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        
        print(f"✅ Chunked AI analysis report generated: purdue_hackers_chunked_ai_analysis.md")
        print(f"📊 Total Projects: {len(projects)}")
        print(f"🧩 Chunks Processed: {total_chunks}")
        print(f"📁 Categories: {len(set(p.get('category') for p in projects))}")
        print(f"🔧 Technologies: {len(set(tech for p in projects for tech in p.get('technologies', [])))}")
        
        # Show category breakdown
        categories = {}
        for project in projects:
            cat = project.get('category', 'Other')
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n📈 Category Breakdown:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {cat}: {count} projects")
        
    except FileNotFoundError:
        print("❌ chunked_ai_results.json not found. Run the chunked analyzer first.")
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    convert_chunked_results() 