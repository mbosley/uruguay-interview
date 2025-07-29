#!/usr/bin/env python3
"""
Theme Consolidation Script
Aggregates interview-specific themes into meta-themes using AI

This script:
1. Loads all themes from enriched interviews
2. Uses an LLM to cluster and consolidate themes
3. Creates a mapping from specific themes to meta-themes
4. Updates the enriched corpus with meta-theme mappings
"""

import json
import os
import glob
from typing import Dict, List, Set, Tuple
from collections import defaultdict
import asyncio
from datetime import datetime
import argparse

from dotenv import load_dotenv
from interview_research_agent_improved import InterviewResearchAgent

# Load environment variables
load_dotenv()

# Predetermined issue tags for stable categorization
ISSUE_TAGS = {
    "healthcare": {
        "name": "Healthcare",
        "description": "Health services, hospitals, medication access, mental health",
        "keywords": ["health", "salud", "hospital", "medication", "medical", "doctor", "nurse", "clinic", "mental", "psychiatric"]
    },
    "education": {
        "name": "Education", 
        "description": "Schools, teachers, curriculum, educational quality, youth education",
        "keywords": ["education", "educación", "school", "escuela", "teacher", "maestro", "student", "learning", "curriculum"]
    },
    "economy": {
        "name": "Economy",
        "description": "Employment, jobs, economic development, business, productivity",
        "keywords": ["economy", "economía", "employment", "empleo", "work", "trabajo", "business", "industry", "productive"]
    },
    "security": {
        "name": "Security",
        "description": "Crime, violence, drug trafficking, police, public safety",
        "keywords": ["security", "seguridad", "crime", "delito", "drug", "droga", "violence", "police", "policía", "safety"]
    },
    "infrastructure": {
        "name": "Infrastructure",
        "description": "Roads, utilities, internet, public works, transportation",
        "keywords": ["infrastructure", "road", "camino", "internet", "water", "agua", "electricity", "transport", "connectivity"]
    },
    "housing": {
        "name": "Housing",
        "description": "Housing access, affordability, homelessness, cooperative housing",
        "keywords": ["housing", "vivienda", "home", "casa", "rent", "alquiler", "cooperative", "homeless", "shelter"]
    },
    "governance": {
        "name": "Governance",
        "description": "Government services, bureaucracy, public administration, policy",
        "keywords": ["government", "gobierno", "bureaucracy", "burocracia", "administration", "policy", "institutional", "corruption"]
    },
    "social_welfare": {
        "name": "Social Welfare",
        "description": "Social services, elderly care, disability support, vulnerable populations",
        "keywords": ["social", "elderly", "anciano", "disability", "discapacidad", "welfare", "assistance", "vulnerable", "care"]
    },
    "rural_development": {
        "name": "Rural Development",
        "description": "Rural areas, agriculture, countryside development, rural-urban divide",
        "keywords": ["rural", "countryside", "campo", "agriculture", "farming", "interior", "village", "pueblo"]
    },
    "environment": {
        "name": "Environment",
        "description": "Environmental issues, pollution, sustainability, climate",
        "keywords": ["environment", "ambiente", "pollution", "contamination", "climate", "sustainable", "ecology", "water quality"]
    },
    "culture": {
        "name": "Culture",
        "description": "Cultural identity, heritage, traditions, community values",
        "keywords": ["culture", "cultura", "heritage", "patrimonio", "tradition", "identity", "community", "values"]
    },
    "youth": {
        "name": "Youth",
        "description": "Youth issues, opportunities, challenges facing young people",
        "keywords": ["youth", "joven", "young", "adolescent", "teenager", "future", "opportunity", "generation"]
    }
}


def load_all_themes() -> Dict[str, List[Dict]]:
    """Load all themes from enriched interviews"""
    themes_by_interview = {}
    all_themes = []
    theme_occurrences = defaultdict(list)
    
    # Load enriched files
    enriched_files = glob.glob("../data/processed/enriched/*_enriched.json")
    
    for file_path in enriched_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            interview_id = data.get('interview_id')
            annotation = data.get('annotation', {})
            summary = annotation.get('summary', {})
            key_themes = summary.get('key_themes', [])
            
            # Store themes for this interview
            themes_by_interview[interview_id] = key_themes
            
            # Collect all theme names and their contexts
            for theme_obj in key_themes:
                if isinstance(theme_obj, dict) and 'theme' in theme_obj:
                    theme_name = theme_obj['theme']
                    theme_occurrences[theme_name].append({
                        'interview_id': interview_id,
                        'description': theme_obj.get('description', ''),
                        'intensity': theme_obj.get('intensity', ''),
                        'tags': theme_obj.get('tags', [])
                    })
                    
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return themes_by_interview, theme_occurrences


async def consolidate_themes_with_ai(theme_occurrences: Dict[str, List[Dict]], 
                                   provider: str = "groq") -> Dict[str, Dict]:
    """Use AI to consolidate themes into meta-themes"""
    
    # Prepare theme data for AI analysis
    theme_summary = []
    for theme_name, occurrences in theme_occurrences.items():
        theme_summary.append({
            'theme': theme_name,
            'occurrence_count': len(occurrences),
            'sample_descriptions': [occ['description'][:200] for occ in occurrences[:3] if occ['description']],
            'common_tags': list(set(tag for occ in occurrences for tag in occ.get('tags', [])))[:10]
        })
    
    # Create prompt for theme consolidation
    consolidation_prompt = f"""
You are analyzing themes from 35 citizen consultation interviews from Uruguay. 
There are {len(theme_summary)} unique themes that need to be consolidated into 10-15 meta-themes.

Here are all the themes with their occurrence counts and sample descriptions:

{json.dumps(theme_summary, indent=2, ensure_ascii=False)}

Your task is to:
1. Identify 10-15 high-level meta-themes that capture the main concerns across all interviews
2. Map each specific theme to the most appropriate meta-theme
3. Provide a clear description for each meta-theme
4. Ensure meta-themes are distinct and cover all major areas of citizen concern

Return a JSON object with this structure:
{{
    "meta_themes": {{
        "meta_theme_id": {{
            "name": "Human-readable meta-theme name",
            "description": "Clear description of what this meta-theme encompasses",
            "keywords": ["key", "words", "for", "this", "theme"],
            "mapped_themes": ["list", "of", "original", "theme", "names", "that", "map", "here"]
        }}
    }},
    "theme_mapping": {{
        "original_theme_name": "meta_theme_id"
    }}
}}

Focus on creating meta-themes that reflect major policy areas and citizen concerns like:
- Healthcare and public health
- Education and youth development  
- Security and crime prevention
- Economic development and employment
- Infrastructure and public services
- Social inclusion and equality
- Governance and institutional trust
- Rural vs urban disparities
- etc.

Ensure every original theme is mapped to exactly one meta-theme.
"""

    # Initialize agent
    agent = InterviewResearchAgent(
        provider=provider,
        verbose=True
    )
    
    # Get consolidation from AI
    print("\nConsolidating themes with AI...")
    try:
        # Check if the provider uses async or sync calls
        if provider == "groq":
            # Groq uses synchronous calls
            response = agent.client.chat.completions.create(
                model=agent.model,
                messages=[
                    {"role": "system", "content": "You are an expert in qualitative research and thematic analysis."},
                    {"role": "user", "content": consolidation_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
        else:
            # Other providers might use async
            response = await agent.client.chat.completions.create(
                model=agent.model,
                messages=[
                    {"role": "system", "content": "You are an expert in qualitative research and thematic analysis."},
                    {"role": "user", "content": consolidation_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        print(f"Error in AI consolidation: {e}")
        import traceback
        traceback.print_exc()
        return None


def map_themes_to_issue_tags(theme_mapping: Dict[str, str], meta_themes: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Map each theme to relevant issue tags based on keywords"""
    theme_to_tags = {}
    
    for theme_name, meta_theme_id in theme_mapping.items():
        matched_tags = set()
        
        # Get the meta-theme data
        meta_theme_data = meta_themes.get(meta_theme_id, {})
        
        # Check theme name and meta-theme name/description against keywords
        theme_lower = theme_name.lower()
        meta_name_lower = meta_theme_data.get('name', '').lower()
        meta_desc_lower = meta_theme_data.get('description', '').lower()
        
        # Check against each issue tag's keywords
        for tag_id, tag_data in ISSUE_TAGS.items():
            for keyword in tag_data['keywords']:
                if (keyword in theme_lower or 
                    keyword in meta_name_lower or 
                    keyword in meta_desc_lower):
                    matched_tags.add(tag_id)
                    break
        
        # If no tags matched, try to assign based on meta-theme
        if not matched_tags:
            # Use some heuristics based on meta-theme ID
            if 'health' in meta_theme_id:
                matched_tags.add('healthcare')
            elif 'education' in meta_theme_id:
                matched_tags.add('education')
            elif 'employ' in meta_theme_id or 'economic' in meta_theme_id:
                matched_tags.add('economy')
            elif 'security' in meta_theme_id or 'drug' in meta_theme_id:
                matched_tags.add('security')
            elif 'housing' in meta_theme_id:
                matched_tags.add('housing')
            elif 'infrastruct' in meta_theme_id:
                matched_tags.add('infrastructure')
            elif 'govern' in meta_theme_id or 'bureaucrat' in meta_theme_id:
                matched_tags.add('governance')
            elif 'social' in meta_theme_id or 'elderly' in meta_theme_id or 'disab' in meta_theme_id:
                matched_tags.add('social_welfare')
            elif 'rural' in meta_theme_id:
                matched_tags.add('rural_development')
            elif 'environ' in meta_theme_id:
                matched_tags.add('environment')
            elif 'cultur' in meta_theme_id or 'heritage' in meta_theme_id:
                matched_tags.add('culture')
            elif 'poverty' in meta_theme_id:
                matched_tags.add('social_welfare')
        
        theme_to_tags[theme_name] = list(matched_tags)
    
    return theme_to_tags


def save_theme_mapping(consolidation_result: Dict, output_path: str):
    """Save the theme consolidation results"""
    
    # Add metadata
    consolidation_result['metadata'] = {
        'created_at': datetime.now().isoformat(),
        'total_original_themes': len(consolidation_result.get('theme_mapping', {})),
        'total_meta_themes': len(consolidation_result.get('meta_themes', {})),
        'total_issue_tags': len(ISSUE_TAGS),
        'issue_tags': ISSUE_TAGS
    }
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(consolidation_result, f, indent=2, ensure_ascii=False)
    
    print(f"\nTheme mapping saved to: {output_path}")


def update_enriched_files_with_mappings(theme_mapping: Dict[str, str], 
                                       theme_to_tags: Dict[str, List[str]]):
    """Update enriched interview files with meta-theme and issue tag mappings"""
    
    enriched_files = glob.glob("../data/processed/enriched/*_enriched.json")
    updated_count = 0
    
    for file_path in enriched_files:
        try:
            # Load existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update themes with meta-theme mappings and issue tags
            annotation = data.get('annotation', {})
            summary = annotation.get('summary', {})
            key_themes = summary.get('key_themes', [])
            
            # Collect all issue tags for this interview
            interview_issue_tags = set()
            
            # Add meta_theme and issue_tags fields to each theme
            updated = False
            for theme_obj in key_themes:
                if isinstance(theme_obj, dict) and 'theme' in theme_obj:
                    theme_name = theme_obj['theme']
                    if theme_name in theme_mapping:
                        theme_obj['meta_theme'] = theme_mapping[theme_name]
                        updated = True
                    
                    if theme_name in theme_to_tags:
                        theme_obj['issue_tags'] = theme_to_tags[theme_name]
                        interview_issue_tags.update(theme_to_tags[theme_name])
                        updated = True
            
            # Add aggregated issue tags at the annotation level
            if updated:
                annotation['issue_tags'] = sorted(list(interview_issue_tags))
                
                # Save updated file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                updated_count += 1
                
        except Exception as e:
            print(f"Error updating {file_path}: {e}")
    
    print(f"\nUpdated {updated_count} enriched files with meta-theme and issue tag mappings")


def print_consolidation_summary(consolidation_result: Dict):
    """Print a summary of the theme consolidation"""
    
    meta_themes = consolidation_result.get('meta_themes', {})
    theme_mapping = consolidation_result.get('theme_mapping', {})
    
    print("\n" + "="*80)
    print("THEME CONSOLIDATION SUMMARY")
    print("="*80)
    
    print(f"\nTotal meta-themes: {len(meta_themes)}")
    print(f"Total original themes mapped: {len(theme_mapping)}")
    
    print("\nMETA-THEMES:")
    for meta_id, meta_data in meta_themes.items():
        print(f"\n{meta_id}: {meta_data['name']}")
        print(f"  Description: {meta_data['description']}")
        print(f"  Mapped themes: {len(meta_data['mapped_themes'])}")
        print(f"  Examples: {', '.join(meta_data['mapped_themes'][:3])}")
        if len(meta_data['mapped_themes']) > 3:
            print(f"           ... and {len(meta_data['mapped_themes']) - 3} more")


async def main():
    """Main consolidation pipeline"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Consolidate interview themes into meta-themes')
    parser.add_argument('--provider', type=str, default='groq', 
                       choices=['moonshot', 'groq', 'openai', 'gemini'],
                       help='LLM provider to use (default: groq)')
    args = parser.parse_args()
    
    print("Theme Consolidation Pipeline")
    print("="*50)
    print(f"Using provider: {args.provider}")
    
    # Step 1: Load all themes
    print("\n1. Loading themes from enriched interviews...")
    themes_by_interview, theme_occurrences = load_all_themes()
    
    print(f"   - Found {len(themes_by_interview)} interviews")
    print(f"   - Found {len(theme_occurrences)} unique themes")
    
    # Show most common themes
    print("\n   Most common themes:")
    sorted_themes = sorted(theme_occurrences.items(), key=lambda x: len(x[1]), reverse=True)
    for theme, occurrences in sorted_themes[:10]:
        print(f"   - {theme}: {len(occurrences)} interviews")
    
    # Step 2: Consolidate with AI
    print("\n2. Consolidating themes with AI...")
    consolidation_result = await consolidate_themes_with_ai(theme_occurrences, provider=args.provider)
    
    if not consolidation_result:
        print("Error: Failed to consolidate themes")
        return
    
    # Step 3: Map themes to issue tags
    print("\n3. Mapping themes to issue tags...")
    theme_mapping = consolidation_result.get('theme_mapping', {})
    meta_themes = consolidation_result.get('meta_themes', {})
    theme_to_tags = map_themes_to_issue_tags(theme_mapping, meta_themes)
    
    # Add issue tag mapping to consolidation result
    consolidation_result['theme_to_issue_tags'] = theme_to_tags
    
    # Step 4: Save theme mapping
    output_path = "../data/processed/enriched/theme_consolidation.json"
    save_theme_mapping(consolidation_result, output_path)
    
    # Step 5: Print summary
    print_consolidation_summary(consolidation_result)
    
    # Print issue tag summary
    print("\nISSUE TAG MAPPING:")
    tag_counts = defaultdict(int)
    for tags in theme_to_tags.values():
        for tag in tags:
            tag_counts[tag] += 1
    
    for tag_id, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True):
        tag_name = ISSUE_TAGS[tag_id]['name']
        print(f"  {tag_name}: {count} themes")
    
    # Step 6: Update enriched files
    print("\n4. Updating enriched files with meta-theme and issue tag mappings...")
    update_enriched_files_with_mappings(theme_mapping, theme_to_tags)
    
    print("\nTheme consolidation complete!")


if __name__ == "__main__":
    asyncio.run(main())