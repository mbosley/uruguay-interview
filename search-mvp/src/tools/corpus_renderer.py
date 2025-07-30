"""Render corpus-level data (statistics, themes) as readable plain text"""

import json
import textwrap
from typing import Dict, Any, List, Optional


class CorpusRenderer:
    """Render corpus statistics and themes in a human-readable format"""
    
    def __init__(self, max_width: int = 80):
        self.max_width = max_width
        self.wrapper = textwrap.TextWrapper(
            width=max_width,
            break_long_words=False,
            break_on_hyphens=False
        )
    
    def render(self, data: str) -> str:
        """Render corpus data from JSON string to readable text"""
        try:
            parsed = json.loads(data)
            
            # Determine the type of data and render accordingly
            if parsed.get("total_interviews") and parsed.get("total_turns"):
                return self._render_corpus_stats(parsed)
            elif parsed.get("meta_themes") or (parsed.get("themes") and not parsed.get("interview_id")):
                return self._render_all_themes(parsed)
            elif parsed.get("type") == "aggregated_search_results":
                return self._render_aggregated_search(parsed)
            elif parsed.get("type") == "theme_hierarchy" and parsed.get("total_themes"):
                return self._render_theme_search(parsed)
            elif parsed.get("type") == "search_results":
                return self._render_search_results(parsed)
            else:
                # Fallback to original JSON if structure unknown
                return data
                
        except (json.JSONDecodeError, KeyError):
            # Return original if not valid JSON
            return data
    
    def _render_corpus_stats(self, data: Dict[str, Any]) -> str:
        """Render corpus statistics in readable format"""
        lines = []
        
        # Header - no lines needed, content speaks for itself
        lines.append("📊 CORPUS STATISTICS")
        
        # Basic stats
        lines.append(f"\n📚 Total interviews: {data.get('total_interviews', 0)}")
        lines.append(f"💬 Total conversation turns: {data.get('total_turns', 0):,}")
        
        # Average turns - check both possible field names
        avg_turns = data.get('avg_turns_per_interview', data.get('average_turns_per_interview', 0))
        lines.append(f"📈 Average turns per interview: {avg_turns:.1f}")
        
        # Total themes - check both possible field names
        total_themes = data.get('unique_themes', data.get('total_themes', 0))
        lines.append(f"\n🎯 Unique themes identified: {total_themes}")
        
        # Additional stats if available
        if data.get('unique_meta_themes'):
            lines.append(f"📂 Meta-themes: {data.get('unique_meta_themes')}")
        
        # Show meta-theme breakdown if available
        if data.get('meta_theme_breakdown'):
            lines.append(f"\n🎯 META-THEME CATEGORIES:")
            
            breakdown = data.get('meta_theme_breakdown', {})
            # Sort by theme count
            sorted_meta = sorted(
                breakdown.items(),
                key=lambda x: x[1].get('theme_count', 0),
                reverse=True
            )
            
            for meta_key, meta_info in sorted_meta:
                theme_count = meta_info.get('theme_count', 0)
                name = meta_info.get('name', meta_key)
                if meta_key != 'uncategorized':
                    key_display = f"  • {name} [{meta_key}] ({theme_count} themes)"
                    lines.append(key_display)
            
            # Show uncategorized separately if exists
            if 'uncategorized' in breakdown:
                uncategorized_count = breakdown['uncategorized'].get('theme_count', 0)
                if uncategorized_count > 0:
                    lines.append(f"\n  📌 Plus {uncategorized_count} uncategorized themes")
            
            lines.append(f"\n💡 Use explore_meta_theme with the key in brackets to explore specific categories")
        
        if data.get('unique_issue_tags'):
            lines.append(f"\n🏷️  Issue tags: {data.get('unique_issue_tags')}")
        
        if data.get('unique_speakers'):
            lines.append(f"👥 Unique speakers: {data.get('unique_speakers')}")
        
        if data.get('total_notable_quotes'):
            lines.append(f"💬 Notable quotes: {data.get('total_notable_quotes')}")
        
        return "\n".join(lines)
    
    def _render_all_themes(self, data: Dict[str, Any]) -> str:
        """Render all themes listing in readable format"""
        lines = []
        
        # Header - no lines needed
        lines.append("🎯 INTERVIEW THEMES ACROSS CORPUS")
        
        # Check if we have meta-themes (hierarchical structure)
        if "meta_themes" in data:
            return self._render_meta_themes(data)
        
        # Simple theme listing
        themes = data.get("themes", {})
        if isinstance(themes, dict):
            # Sort themes by frequency (number of interviews)
            sorted_themes = sorted(themes.items(), key=lambda x: len(x[1]) if isinstance(x[1], list) else 0, reverse=True)
            
            # Stats
            total_themes = len(themes)
            lines.append(f"\n📊 Total unique themes: {total_themes}")
            
            # Group by frequency
            high_freq = [(t, interviews) for t, interviews in sorted_themes if len(interviews) >= 5]
            med_freq = [(t, interviews) for t, interviews in sorted_themes if 2 <= len(interviews) < 5]
            low_freq = [(t, interviews) for t, interviews in sorted_themes if len(interviews) == 1]
            
            if high_freq:
                lines.append(f"\n🔥 HIGH FREQUENCY THEMES ({len(high_freq)} themes, 5+ interviews):")
                for theme, interviews in high_freq[:10]:  # Top 10
                    count = len(interviews)
                    lines.append(f"  • {theme} ({count} interviews)")
            
            if med_freq:
                lines.append(f"\n📌 MEDIUM FREQUENCY THEMES ({len(med_freq)} themes, 2-4 interviews):")
                for theme, interviews in med_freq[:10]:  # Top 10
                    count = len(interviews)
                    lines.append(f"  • {theme} ({count} interviews)")
            
            if low_freq:
                lines.append(f"\n📍 UNIQUE THEMES ({len(low_freq)} themes, 1 interview each)")
                # Just show count, not all themes
                lines.append(f"  ({len(low_freq)} themes appearing in single interviews)")
        
        return "\n".join(lines)
    
    def _render_meta_themes(self, data: Dict[str, Any]) -> str:
        """Render hierarchical meta-themes structure"""
        lines = []
        
        # Header already added
        meta_themes = data.get("meta_themes", {})
        
        # Count totals
        total_themes = sum(
            len(meta_data.get("themes", {})) 
            for meta_data in meta_themes.values() 
            if isinstance(meta_data, dict)
        )
        
        # Check if this is filtered to a specific meta-theme
        if data.get("meta_theme_filter") and len(meta_themes) == 1:
            # Detailed view for single meta-theme
            meta_key, meta_data = list(meta_themes.items())[0]
            lines.append(f"\n📊 Exploring: {meta_data.get('name', meta_key)}")
            lines.append(f"Total themes in this category: {len(meta_data.get('themes', {}))}")
            
            themes = meta_data.get("themes", {})
            if themes:
                lines.append(f"\n🎯 THEMES AND OCCURRENCES:")
                
                # Sort themes by total turns
                sorted_themes = sorted(
                    themes.items(),
                    key=lambda x: x[1].get("total_turns", 0),
                    reverse=True
                )
                
                # Group themes by turn count for more compact display
                turn_groups = {}
                for theme_name, theme_data in sorted_themes:
                    turns = theme_data.get("total_turns", 0)
                    interviews = theme_data.get("interviews", [])
                    
                    if turns not in turn_groups:
                        turn_groups[turns] = []
                    turn_groups[turns].append((theme_name, interviews))
                
                # Display grouped themes
                for turn_count in sorted(turn_groups.keys(), reverse=True):
                    themes_in_group = turn_groups[turn_count]
                    lines.append(f"\n📊 {turn_count} turns:")
                    
                    for theme_name, interviews in themes_in_group:
                        # Compact format: theme name + interview
                        if interviews:
                            interview_str = f" [[{interviews[0]}:summary]]"
                            if len(interviews) > 1:
                                interview_str += f" +{len(interviews)-1}"
                        else:
                            interview_str = ""
                        lines.append(f"  • {theme_name}{interview_str}")
        else:
            # Summary view for all meta-themes
            lines.append(f"\n📊 Total themes: {total_themes} across {len(meta_themes)} meta-themes")
            
            # Just show a summary of meta-themes
            lines.append(f"\n🎯 META-THEME CATEGORIES:")
            
            # Sort meta-themes by number of themes
            sorted_meta = sorted(
                [(k, v) for k, v in meta_themes.items() if isinstance(v, dict) and k != "uncategorized"],
                key=lambda x: len(x[1].get("themes", {})),
                reverse=True
            )
            
            for meta_theme, meta_data in sorted_meta[:10]:  # Top 10 categories
                theme_count = len(meta_data.get("themes", {}))
                theme_name = meta_data.get("name", meta_theme)
                lines.append(f"  • {theme_name} ({theme_count} themes)")
            
            if len(sorted_meta) > 10:
                lines.append(f"  ... and {len(sorted_meta) - 10} more categories")
            
            # Note about uncategorized
            if "uncategorized" in meta_themes:
                uncategorized_data = meta_themes["uncategorized"]
                if isinstance(uncategorized_data, dict):
                    uncategorized_count = len(uncategorized_data.get("themes", {}))
                    if uncategorized_count > 0:
                        lines.append(f"\n  📌 Plus {uncategorized_count} uncategorized themes")
            
            lines.append(f"\n💡 Use explore_meta_theme to explore specific categories")
        
        return "\n".join(lines)
    
    def _render_aggregated_search(self, data: Dict[str, Any]) -> str:
        """Render aggregated search results in readable format"""
        lines = []
        
        # Header - no lines needed
        lines.append(f"🔍 SEARCH RESULTS: \"{data.get('query', '')}\"")
        
        # Summary stats
        total_matches = data.get('total_matches', 0)
        interviews_with_matches = data.get('interviews_with_matches', 0)
        
        if total_matches == 0:
            lines.append(f"\n❌ No matches found")
            lines.append("\n💡 Search tips:")
            lines.append("  • Try broader terms or synonyms")
            lines.append("  • Check Spanish spelling (e.g., 'abandonó' not 'abandono')")
            lines.append("  • Use partial phrases instead of exact quotes")
            lines.append("  • Search in Spanish - citizens spoke in Spanish")
        else:
            lines.append(f"\n📊 Found {total_matches} matches across {interviews_with_matches} interviews")
            
            # Top interviews
            top_interviews = data.get('top_interviews', [])
            if top_interviews:
                lines.append(f"\n🎯 TOP INTERVIEWS BY MATCH COUNT:")
                for i, interview in enumerate(top_interviews, 1):
                    interview_id = interview.get('interview_id', '')
                    match_count = interview.get('match_count', 0)
                    sample_turns = interview.get('sample_turns', [])
                    
                    lines.append(f"\n{i}. Interview {interview_id} ({match_count} matches)")
                    if sample_turns:
                        lines.append(f"   Sample turns: {', '.join(sample_turns)}")
        
        return "\n".join(lines)
    
    def _render_search_results(self, data: Dict[str, Any]) -> str:
        """Render search results with informative messages"""
        lines = []
        
        # Header
        query = data.get('query', '')
        lines.append(f"🔍 SEARCH RESULTS: \"{query}\"")
        
        total_results = data.get('total_results', 0)
        results = data.get('results', [])
        
        if total_results == 0:
            lines.append(f"\n❌ No matches found")
            lines.append("\n💡 Search tips:")
            lines.append("  • Try broader terms or synonyms")
            lines.append("  • Check Spanish spelling (e.g., 'abandonó' not 'abandono')")
            lines.append("  • Use partial phrases instead of exact quotes")
            lines.append("  • Search in Spanish - citizens spoke in Spanish")
        else:
            lines.append(f"\n📊 Found {total_results} matches")
            
            # Group results by type if needed
            theme_matches = [r for r in results if r.get('type') == 'theme_match']
            tag_matches = [r for r in results if r.get('type') == 'tag_match']
            text_matches = [r for r in results if r.get('type') == 'turn_text_match']
            
            parts = []
            if theme_matches:
                parts.append(f"{len(theme_matches)} theme matches")
            if tag_matches:
                parts.append(f"{len(tag_matches)} tag matches")
            if text_matches:
                parts.append(f"{len(text_matches)} text matches")
            
            if parts:
                lines.append(f"  • {', '.join(parts)}")
        
        return "\n".join(lines)
    
    def _render_theme_search(self, data: Dict[str, Any]) -> str:
        """Render theme search results in readable format"""
        lines = []
        
        # Header - no lines needed
        lines.append(f"🔍 THEME SEARCH RESULTS")
        
        # Summary
        total_themes = data.get('total_themes', 0)
        lines.append(f"\n📊 Found {total_themes} matching themes")
        
        # Themes by meta-theme
        meta_themes = data.get('meta_themes', {})
        if meta_themes:
            lines.append(f"\n🎯 MATCHING THEMES BY CATEGORY:")
            
            for meta_key, meta_data in meta_themes.items():
                if isinstance(meta_data, dict):
                    meta_name = meta_data.get('name', meta_key)
                    themes = meta_data.get('themes', {})
                    
                    if themes:
                        lines.append(f"\n📂 {meta_name}")
                        for theme_name, theme_info in themes.items():
                            lines.append(f"  • {theme_name}")
                            lines.append(f"    {theme_info}")
        
        return "\n".join(lines)