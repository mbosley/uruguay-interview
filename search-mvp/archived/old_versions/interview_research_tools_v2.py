"""
Enhanced Interview Research Tools v2
Tools updated to leverage hierarchical theme structure (issue tags → meta-themes → themes)
"""

import json
import os
from typing import List, Dict, Any, Optional, Set, Tuple
from pathlib import Path
import re
from collections import defaultdict

class EnhancedInterviewTools:
    def __init__(self, corpus_path: str = "../data/processed/enriched"):
        self.corpus_path = Path(corpus_path)
        self.corpus_data = None
        self.theme_mapping = None
        self.issue_tags = None
        self._load_corpus()
        self._load_theme_consolidation()
    
    def _load_corpus(self):
        """Load the enriched corpus"""
        try:
            # Load individual enriched files
            self.corpus_data = {}
            for json_file in self.corpus_path.glob("*_enriched.json"):
                if not json_file.name.startswith("_"):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        interview_id = data.get('interview_id')
                        if interview_id:
                            self.corpus_data[interview_id] = data
            
            print(f"✓ Loaded {len(self.corpus_data)} enriched interviews")
        except Exception as e:
            print(f"Error loading corpus: {e}")
            self.corpus_data = {}
    
    def _load_theme_consolidation(self):
        """Load theme consolidation mapping"""
        try:
            consolidation_path = self.corpus_path / "theme_consolidation.json"
            if consolidation_path.exists():
                with open(consolidation_path, 'r', encoding='utf-8') as f:
                    consolidation = json.load(f)
                    self.theme_mapping = consolidation.get('theme_mapping', {})
                    self.meta_themes = consolidation.get('meta_themes', {})
                    self.issue_tags = consolidation.get('metadata', {}).get('issue_tags', {})
                    self.theme_to_issue_tags = consolidation.get('theme_to_issue_tags', {})
                print(f"✓ Loaded theme consolidation: {len(self.meta_themes)} meta-themes, {len(self.issue_tags)} issue tags")
            else:
                print("⚠ Theme consolidation not found - run 'make consolidate' first")
                self.theme_mapping = {}
                self.meta_themes = {}
                self.issue_tags = {}
        except Exception as e:
            print(f"Error loading theme consolidation: {e}")
    
    def explore_by_issue_tag(self, issue_tag: str) -> Dict[str, Any]:
        """
        Explore interviews by high-level issue tag (e.g., 'healthcare', 'education')
        Returns structured data about themes and interviews related to this issue
        """
        if issue_tag not in self.issue_tags:
            available_tags = list(self.issue_tags.keys())
            return {
                "error": f"Issue tag '{issue_tag}' not found",
                "available_tags": available_tags,
                "suggestion": f"Try one of: {', '.join(available_tags[:5])}"
            }
        
        # Find all themes associated with this issue tag
        related_themes = []
        for theme, tags in self.theme_to_issue_tags.items():
            if issue_tag in tags:
                related_themes.append(theme)
        
        # Group themes by meta-theme
        meta_theme_groups = defaultdict(list)
        for theme in related_themes:
            meta_theme_id = self.theme_mapping.get(theme)
            if meta_theme_id:
                meta_theme_groups[meta_theme_id].append(theme)
        
        # Find interviews containing these themes
        relevant_interviews = []
        theme_excerpts = defaultdict(list)
        
        for interview_id, interview in self.corpus_data.items():
            annotation = interview.get('annotation', {})
            issue_tags_in_interview = annotation.get('issue_tags', [])
            
            if issue_tag in issue_tags_in_interview:
                # Get themes and excerpts from this interview
                summary = annotation.get('summary', {})
                key_themes = summary.get('key_themes', [])
                
                interview_themes = []
                for theme_obj in key_themes:
                    if isinstance(theme_obj, dict):
                        theme_name = theme_obj.get('theme')
                        if theme_name in related_themes:
                            interview_themes.append(theme_name)
                            
                            # Collect primary evidence
                            for evidence in theme_obj.get('primary_evidence', []):
                                theme_excerpts[theme_name].append({
                                    'interview_id': interview_id,
                                    'turn': evidence.get('turn'),
                                    'quote': evidence.get('quote')
                                })
                
                if interview_themes:
                    relevant_interviews.append({
                        'interview_id': interview_id,
                        'themes': interview_themes,
                        'location': annotation.get('tags', {}).get('location', []),
                        'summary': summary.get('overview', '')[:200] + '...'
                    })
        
        return {
            'issue_tag': issue_tag,
            'description': self.issue_tags[issue_tag]['description'],
            'total_themes': len(related_themes),
            'total_interviews': len(relevant_interviews),
            'meta_theme_breakdown': {
                meta_id: {
                    'name': self.meta_themes[meta_id]['name'],
                    'description': self.meta_themes[meta_id]['description'],
                    'themes': themes
                }
                for meta_id, themes in meta_theme_groups.items()
            },
            'sample_interviews': relevant_interviews[:5],
            'key_excerpts': {
                theme: excerpts[:3] 
                for theme, excerpts in sorted(
                    theme_excerpts.items(), 
                    key=lambda x: len(x[1]), 
                    reverse=True
                )[:5]
            }
        }
    
    def explore_by_meta_theme(self, meta_theme_id: str) -> Dict[str, Any]:
        """
        Explore interviews by meta-theme (consolidated theme group)
        """
        if meta_theme_id not in self.meta_themes:
            return {
                "error": f"Meta-theme '{meta_theme_id}' not found",
                "available_meta_themes": list(self.meta_themes.keys())
            }
        
        meta_theme_data = self.meta_themes[meta_theme_id]
        mapped_themes = meta_theme_data.get('mapped_themes', [])
        
        # Find all interviews containing these themes
        relevant_interviews = []
        theme_distribution = defaultdict(int)
        location_distribution = defaultdict(int)
        
        for interview_id, interview in self.corpus_data.items():
            annotation = interview.get('annotation', {})
            summary = annotation.get('summary', {})
            key_themes = summary.get('key_themes', [])
            
            interview_themes = []
            interview_excerpts = []
            
            for theme_obj in key_themes:
                if isinstance(theme_obj, dict):
                    theme_name = theme_obj.get('theme')
                    if theme_name in mapped_themes:
                        interview_themes.append(theme_name)
                        theme_distribution[theme_name] += 1
                        
                        # Get best excerpt
                        evidence = theme_obj.get('primary_evidence', [])
                        if evidence:
                            interview_excerpts.append({
                                'theme': theme_name,
                                'quote': evidence[0].get('quote', ''),
                                'turn': evidence[0].get('turn', '')
                            })
            
            if interview_themes:
                location = annotation.get('tags', {}).get('location', [])
                if location:
                    location_distribution[location[0]] += 1
                
                relevant_interviews.append({
                    'interview_id': interview_id,
                    'themes': interview_themes,
                    'location': location,
                    'key_excerpt': interview_excerpts[0] if interview_excerpts else None,
                    'theme_count': len(interview_themes)
                })
        
        # Sort interviews by theme count
        relevant_interviews.sort(key=lambda x: x['theme_count'], reverse=True)
        
        return {
            'meta_theme_id': meta_theme_id,
            'meta_theme_name': meta_theme_data['name'],
            'description': meta_theme_data['description'],
            'total_interviews': len(relevant_interviews),
            'theme_distribution': dict(sorted(
                theme_distribution.items(), 
                key=lambda x: x[1], 
                reverse=True
            )),
            'location_distribution': dict(sorted(
                location_distribution.items(), 
                key=lambda x: x[1], 
                reverse=True
            )),
            'top_interviews': relevant_interviews[:10],
            'issue_tags': list(set(
                tag for theme in mapped_themes 
                for tag in self.theme_to_issue_tags.get(theme, [])
            ))
        }
    
    def search_themes_semantic(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Search for themes using semantic similarity
        This is a simplified version - could be enhanced with embeddings
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        theme_scores = []
        
        # Score each theme based on overlap with query
        for theme_name, meta_theme_id in self.theme_mapping.items():
            score = 0
            theme_lower = theme_name.lower()
            
            # Direct match bonus
            if query_lower in theme_lower:
                score += 10
            
            # Word overlap
            theme_words = set(theme_lower.replace('_', ' ').split())
            overlap = len(query_words & theme_words)
            score += overlap * 3
            
            # Check meta-theme description
            meta_theme = self.meta_themes.get(meta_theme_id, {})
            desc_lower = meta_theme.get('description', '').lower()
            if query_lower in desc_lower:
                score += 5
            
            # Check against theme descriptions in corpus
            theme_desc_score = 0
            for interview in self.corpus_data.values():
                for theme_obj in interview.get('annotation', {}).get('summary', {}).get('key_themes', []):
                    if isinstance(theme_obj, dict) and theme_obj.get('theme') == theme_name:
                        theme_desc = theme_obj.get('description', '').lower()
                        if query_lower in theme_desc:
                            theme_desc_score += 2
                        break
            
            score += min(theme_desc_score, 10)  # Cap contribution
            
            if score > 0:
                theme_scores.append((theme_name, meta_theme_id, score))
        
        # Sort by score
        theme_scores.sort(key=lambda x: x[2], reverse=True)
        top_themes = theme_scores[:top_k]
        
        # Get details for top themes
        results = []
        for theme_name, meta_theme_id, score in top_themes:
            # Count interviews with this theme
            interview_count = 0
            sample_quotes = []
            
            for interview in self.corpus_data.values():
                for theme_obj in interview.get('annotation', {}).get('summary', {}).get('key_themes', []):
                    if isinstance(theme_obj, dict) and theme_obj.get('theme') == theme_name:
                        interview_count += 1
                        evidence = theme_obj.get('primary_evidence', [])
                        if evidence and len(sample_quotes) < 2:
                            sample_quotes.append(evidence[0].get('quote', ''))
                        break
            
            results.append({
                'theme': theme_name,
                'meta_theme': self.meta_themes.get(meta_theme_id, {}).get('name', ''),
                'relevance_score': score,
                'interview_count': interview_count,
                'issue_tags': self.theme_to_issue_tags.get(theme_name, []),
                'sample_quotes': sample_quotes
            })
        
        return {
            'query': query,
            'total_results': len(theme_scores),
            'top_themes': results
        }
    
    def get_theme_hierarchy(self) -> Dict[str, Any]:
        """
        Get the complete theme hierarchy for navigation
        """
        hierarchy = {}
        
        # Build hierarchy: issue_tag -> meta_theme -> themes
        for issue_tag_id, issue_tag_data in self.issue_tags.items():
            hierarchy[issue_tag_id] = {
                'name': issue_tag_data['name'],
                'description': issue_tag_data['description'],
                'meta_themes': defaultdict(lambda: {'themes': []})
            }
        
        # Populate themes under meta-themes and issue tags
        for theme_name, meta_theme_id in self.theme_mapping.items():
            issue_tags = self.theme_to_issue_tags.get(theme_name, [])
            meta_theme_data = self.meta_themes.get(meta_theme_id, {})
            
            for tag in issue_tags:
                if tag in hierarchy:
                    hierarchy[tag]['meta_themes'][meta_theme_id] = {
                        'name': meta_theme_data.get('name', ''),
                        'themes': hierarchy[tag]['meta_themes'][meta_theme_id]['themes'] + [theme_name]
                    }
        
        # Convert defaultdicts to regular dicts and count
        for issue_tag in hierarchy:
            hierarchy[issue_tag]['meta_themes'] = dict(hierarchy[issue_tag]['meta_themes'])
            hierarchy[issue_tag]['total_themes'] = sum(
                len(mt['themes']) for mt in hierarchy[issue_tag]['meta_themes'].values()
            )
        
        return hierarchy
    
    def analyze_cross_cutting_themes(self, issue_tags: List[str]) -> Dict[str, Any]:
        """
        Analyze themes that appear across multiple issue tags
        Useful for understanding intersectional issues
        """
        if not all(tag in self.issue_tags for tag in issue_tags):
            return {
                "error": "One or more issue tags not found",
                "available_tags": list(self.issue_tags.keys())
            }
        
        # Find themes that appear in multiple specified issue tags
        theme_tag_mapping = defaultdict(set)
        for theme, tags in self.theme_to_issue_tags.items():
            tag_overlap = set(tags) & set(issue_tags)
            if len(tag_overlap) > 1:
                theme_tag_mapping[theme] = tag_overlap
        
        # Analyze interviews that touch on multiple issue areas
        cross_cutting_interviews = []
        
        for interview_id, interview in self.corpus_data.items():
            annotation = interview.get('annotation', {})
            interview_tags = set(annotation.get('issue_tags', []))
            
            overlap = interview_tags & set(issue_tags)
            if len(overlap) > 1:
                # Get themes from this interview
                themes = []
                for theme_obj in annotation.get('summary', {}).get('key_themes', []):
                    if isinstance(theme_obj, dict):
                        theme_name = theme_obj.get('theme')
                        if theme_name in theme_tag_mapping:
                            themes.append({
                                'theme': theme_name,
                                'tags': list(theme_tag_mapping[theme_name])
                            })
                
                if themes:
                    cross_cutting_interviews.append({
                        'interview_id': interview_id,
                        'issue_tags': list(overlap),
                        'cross_cutting_themes': themes,
                        'location': annotation.get('tags', {}).get('location', [])
                    })
        
        return {
            'analyzed_tags': issue_tags,
            'cross_cutting_themes': {
                theme: {
                    'tags': list(tags),
                    'meta_theme': self.meta_themes.get(
                        self.theme_mapping.get(theme, ''), {}
                    ).get('name', '')
                }
                for theme, tags in theme_tag_mapping.items()
            },
            'total_cross_cutting_interviews': len(cross_cutting_interviews),
            'sample_interviews': cross_cutting_interviews[:5]
        }


# Standalone tool functions for the agent
def explore_issue_tag(issue_tag: str) -> str:
    """Explore interviews and themes related to a specific issue tag"""
    tools = EnhancedInterviewTools()
    result = tools.explore_by_issue_tag(issue_tag)
    return json.dumps(result, indent=2, ensure_ascii=False)

def explore_meta_theme(meta_theme_id: str) -> str:
    """Explore interviews related to a specific meta-theme"""
    tools = EnhancedInterviewTools()
    result = tools.explore_by_meta_theme(meta_theme_id)
    return json.dumps(result, indent=2, ensure_ascii=False)

def search_themes(query: str, top_k: int = 10) -> str:
    """Search for themes using semantic similarity"""
    tools = EnhancedInterviewTools()
    result = tools.search_themes_semantic(query, top_k)
    return json.dumps(result, indent=2, ensure_ascii=False)

def get_hierarchy() -> str:
    """Get the complete theme hierarchy"""
    tools = EnhancedInterviewTools()
    result = tools.get_theme_hierarchy()
    return json.dumps(result, indent=2, ensure_ascii=False)

def analyze_intersections(issue_tags: List[str]) -> str:
    """Analyze cross-cutting themes across multiple issue tags"""
    tools = EnhancedInterviewTools()
    result = tools.analyze_cross_cutting_themes(issue_tags)
    return json.dumps(result, indent=2, ensure_ascii=False)