"""
Analytics Dashboard - Statistical analysis of the interview corpus
"""

import streamlit as st
import os
import sys
from collections import defaultdict

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
web_demo_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(web_demo_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, web_demo_dir)

from corpus_loader import load_enriched_corpus

st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

def main():
    st.title("📊 Analytics Dashboard")
    st.markdown("Statistical analysis of themes and patterns across all interviews")
    
    # Load corpus
    with st.spinner("Loading corpus data..."):
        corpus_data = load_enriched_corpus()
    
    if not corpus_data['interviews']:
        st.error("No interview data found.")
        return
    
    # Get theme consolidation data
    theme_consolidation = corpus_data.get('theme_consolidation', {})
    issue_tags = theme_consolidation.get('metadata', {}).get('issue_tags', {})
    
    # Collect comprehensive analytics data
    theme_counts = {}
    meta_theme_counts = {}
    issue_tag_counts = {}
    location_counts = {}
    demographic_data = {"gender": {}, "age": {}, "occupation": {}}
    intensity_counts = {"high": 0, "medium": 0, "low": 0}
    themes_per_interview = []
    meta_theme_to_themes = {}
    issue_to_meta_themes = {}
    
    # Process all interviews
    for interview_id, interview in corpus_data['interviews'].items():
        annotation = interview.get('annotation', {})
        summary = annotation.get('summary', {})
        key_themes = summary.get('key_themes', [])
        tags = annotation.get('tags', {})
        
        # Count themes per interview
        theme_count = 0
        
        # Extract location
        location_tags = tags.get('location', [])
        location = location_tags[0] if location_tags else 'Unknown'
        location_counts[location] = location_counts.get(location, 0) + 1
        
        # Extract demographics
        for gender in tags.get('gender', []):
            demographic_data["gender"][gender] = demographic_data["gender"].get(gender, 0) + 1
        for age in tags.get('age', []):
            demographic_data["age"][age] = demographic_data["age"].get(age, 0) + 1
        for occupation in tags.get('occupation', []):
            demographic_data["occupation"][occupation] = demographic_data["occupation"].get(occupation, 0) + 1
        
        # Process themes
        for theme_obj in key_themes:
            if isinstance(theme_obj, dict) and 'theme' in theme_obj:
                theme_name = theme_obj['theme']
                theme_count += 1
                theme_counts[theme_name] = theme_counts.get(theme_name, 0) + 1
                
                # Track intensity
                intensity = theme_obj.get('intensity', 'medium').lower()
                if intensity in intensity_counts:
                    intensity_counts[intensity] += 1
                
                # Count meta-themes and build relationships
                if theme_obj.get('meta_theme'):
                    meta_theme = theme_obj['meta_theme']
                    meta_theme_counts[meta_theme] = meta_theme_counts.get(meta_theme, 0) + 1
                    
                    # Track meta-theme to themes mapping
                    if meta_theme not in meta_theme_to_themes:
                        meta_theme_to_themes[meta_theme] = set()
                    meta_theme_to_themes[meta_theme].add(theme_name)
                
                # Count issue tags and build relationships
                for tag in theme_obj.get('issue_tags', []):
                    issue_tag_counts[tag] = issue_tag_counts.get(tag, 0) + 1
                    
                    # Track issue to meta-themes mapping
                    if tag not in issue_to_meta_themes:
                        issue_to_meta_themes[tag] = set()
                    if theme_obj.get('meta_theme'):
                        issue_to_meta_themes[tag].add(theme_obj['meta_theme'])
                    
            elif isinstance(theme_obj, str):
                theme_count += 1
                theme_counts[theme_obj] = theme_counts.get(theme_obj, 0) + 1
        
        themes_per_interview.append(theme_count)
    
    # Calculate averages and statistics
    avg_themes_per_interview = sum(themes_per_interview) / len(themes_per_interview) if themes_per_interview else 0
    
    # Overview metrics
    st.markdown("### 🎯 Overview Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Interviews", len(corpus_data['interviews']))
    with col2:
        st.metric("Unique Themes", len(theme_counts))
    with col3:
        st.metric("Meta-themes", len(meta_theme_counts))
    with col4:
        st.metric("Issue Areas", len(issue_tag_counts))
    with col5:
        st.metric("Avg Themes/Interview", f"{avg_themes_per_interview:.1f}")
    
    st.divider()
    
    # High-level distribution analysis
    st.markdown("### 📊 Theme Distribution Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🏷️ Issue Areas")
        if issue_tag_counts:
            sorted_issue_tags = sorted(issue_tag_counts.items(), key=lambda x: x[1], reverse=True)
            total_mentions = sum(issue_tag_counts.values())
            
            for tag, count in sorted_issue_tags[:8]:
                tag_name = issue_tags.get(tag, {}).get('name', tag)
                percentage = (count / total_mentions * 100) if total_mentions > 0 else 0
                
                # Clean display
                st.markdown(f"**{tag_name}**")
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.progress(count / max(issue_tag_counts.values()) if issue_tag_counts else 0)
                with col_b:
                    st.caption(f"{percentage:.0f}%")
    
    with col2:
        st.markdown("#### 🎯 Top Meta-themes")
        if meta_theme_counts:
            sorted_meta_themes = sorted(meta_theme_counts.items(), key=lambda x: x[1], reverse=True)[:8]
            meta_theme_info = theme_consolidation.get('meta_themes', {})
            
            for meta_theme_id, count in sorted_meta_themes:
                mt_data = meta_theme_info.get(meta_theme_id, {})
                display_name = mt_data.get('name', meta_theme_id)
                
                st.markdown(f"**{display_name}**")
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.progress(count / max(meta_theme_counts.values()) if meta_theme_counts else 0)
                with col_b:
                    st.caption(f"{count}")
    
    with col3:
        st.markdown("#### 📈 Theme Intensity")
        total_intensity = sum(intensity_counts.values())
        if total_intensity > 0:
            # Create a simple stacked representation
            high_pct = intensity_counts.get("high", 0) / total_intensity
            med_pct = intensity_counts.get("medium", 0) / total_intensity
            low_pct = intensity_counts.get("low", 0) / total_intensity
            
            st.markdown("**Distribution:**")
            if high_pct > 0:
                st.markdown(f"🔴 High: **{high_pct*100:.0f}%** ({intensity_counts.get('high', 0)})")
                st.progress(high_pct)
            if med_pct > 0:
                st.markdown(f"🟡 Medium: **{med_pct*100:.0f}%** ({intensity_counts.get('medium', 0)})")
                st.progress(med_pct)
            if low_pct > 0:
                st.markdown(f"🟢 Low: **{low_pct*100:.0f}%** ({intensity_counts.get('low', 0)})")
                st.progress(low_pct)
            
            # Insight
            if high_pct > 0.4:
                st.info("⚠️ High urgency: 40%+ themes marked as high intensity")
    
    st.divider()
    
    # Geographic and Demographic Analysis
    st.markdown("### 🗺️ Geographic & Demographic Distribution")
    
    geo_col1, geo_col2 = st.columns(2)
    
    with geo_col1:
        st.markdown("#### 📍 Location Distribution")
        if location_counts:
            sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
            total_interviews = sum(location_counts.values())
            
            # Group small locations
            major_locations = []
            other_count = 0
            for location, count in sorted_locations:
                if count >= 2 or len(major_locations) < 5:
                    major_locations.append((location, count))
                else:
                    other_count += count
            
            if other_count > 0:
                major_locations.append(("Other locations", other_count))
            
            for location, count in major_locations:
                percentage = (count / total_interviews * 100)
                st.write(f"**{location}**: {count} interviews ({percentage:.1f}%)")
                st.progress(count / total_interviews)
    
    with geo_col2:
        st.markdown("#### 👥 Demographic Insights")
        
        # Gender distribution
        if demographic_data["gender"]:
            st.write("**Gender Distribution:**")
            for gender, count in sorted(demographic_data["gender"].items(), key=lambda x: x[1], reverse=True):
                st.write(f"• {gender}: {count}")
        
        # Age distribution
        if demographic_data["age"]:
            st.write("\n**Age Groups:**")
            for age, count in sorted(demographic_data["age"].items()):
                st.write(f"• {age}: {count}")
        
        # Top occupations
        if demographic_data["occupation"]:
            st.write("\n**Top Occupations:**")
            sorted_occupations = sorted(demographic_data["occupation"].items(), key=lambda x: x[1], reverse=True)[:5]
            for occupation, count in sorted_occupations:
                st.write(f"• {occupation}: {count}")
    
    st.divider()
    
    # Theme Relationship Analysis
    st.markdown("### 🔍 Theme Relationship Analysis")
    
    rel_col1, rel_col2 = st.columns(2)
    
    with rel_col1:
        st.markdown("#### 🔗 Cross-Cutting Themes")
        
        # Find themes that appear across multiple issue areas
        theme_to_issues = {}
        for _, interview in corpus_data['interviews'].items():
            for theme_obj in interview.get('annotation', {}).get('summary', {}).get('key_themes', []):
                if isinstance(theme_obj, dict) and 'theme' in theme_obj:
                    theme = theme_obj['theme']
                    for tag in theme_obj.get('issue_tags', []):
                        if theme not in theme_to_issues:
                            theme_to_issues[theme] = set()
                        theme_to_issues[theme].add(tag)
        
        # Find cross-cutting themes
        cross_cutting = [(theme, issues) for theme, issues in theme_to_issues.items() if len(issues) > 1]
        cross_cutting.sort(key=lambda x: (len(x[1]), theme_counts.get(x[0], 0)), reverse=True)
        
        if cross_cutting:
            st.markdown("**Themes spanning multiple areas:**")
            for theme, issue_set in cross_cutting[:8]:
                issue_names = [issue_tags.get(tag, {}).get('name', tag)[:15] for tag in sorted(issue_set)]
                st.write(f"• **{theme}**")
                st.caption(f"  → {' + '.join(issue_names)} ({theme_counts.get(theme, 0)} interviews)")
        else:
            st.info("No cross-cutting themes found")
    
    with rel_col2:
        st.markdown("#### 🤝 Theme Co-occurrence")
        
        # Calculate theme co-occurrences
        theme_pairs = {}
        for _, interview in corpus_data['interviews'].items():
            themes = []
            for theme_obj in interview.get('annotation', {}).get('summary', {}).get('key_themes', []):
                if isinstance(theme_obj, dict) and 'theme' in theme_obj:
                    themes.append(theme_obj['theme'])
            
            # Count pairs
            for i in range(len(themes)):
                for j in range(i + 1, len(themes)):
                    pair = tuple(sorted([themes[i], themes[j]]))
                    theme_pairs[pair] = theme_pairs.get(pair, 0) + 1
        
        if theme_pairs:
            st.markdown("**Frequently co-occurring themes:**")
            sorted_pairs = sorted(theme_pairs.items(), key=lambda x: x[1], reverse=True)
            
            # Only show strong co-occurrences (at least 3 times)
            strong_pairs = [(pair, count) for pair, count in sorted_pairs if count >= 3][:6]
            
            if strong_pairs:
                for (theme1, theme2), count in strong_pairs:
                    # Shorten theme names for display
                    t1 = theme1[:30] + "..." if len(theme1) > 30 else theme1
                    t2 = theme2[:30] + "..." if len(theme2) > 30 else theme2
                    st.write(f"• **{t1}** ↔ **{t2}**")
                    st.caption(f"  Co-occur in {count} interviews")
            else:
                st.info("No strong co-occurrence patterns found")
        else:
            st.info("Not enough data for co-occurrence analysis")
    
    st.divider()
    
    # Most Prevalent Themes
    st.markdown("### 📋 Theme Prevalence Ranking")
    
    if theme_counts:
        # Create two columns for theme ranking
        rank_col1, rank_col2 = st.columns(2)
        
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Split themes into two columns
        mid_point = len(sorted_themes) // 2
        
        with rank_col1:
            for i, (theme, count) in enumerate(sorted_themes[:mid_point], 1):
                # Find meta-theme
                meta_theme = None
                for mt, themes in meta_theme_to_themes.items():
                    if theme in themes:
                        meta_theme = mt
                        break
                
                st.markdown(f"**{i}.** {theme} ({count})")
                if meta_theme:
                    mt_name = theme_consolidation.get('meta_themes', {}).get(meta_theme, {}).get('name', meta_theme)
                    st.caption(f"   ↳ {mt_name}")
        
        with rank_col2:
            for i, (theme, count) in enumerate(sorted_themes[mid_point:], mid_point + 1):
                # Find meta-theme
                meta_theme = None
                for mt, themes in meta_theme_to_themes.items():
                    if theme in themes:
                        meta_theme = mt
                        break
                
                st.markdown(f"**{i}.** {theme} ({count})")
                if meta_theme:
                    mt_name = theme_consolidation.get('meta_themes', {}).get(meta_theme, {}).get('name', meta_theme)
                    st.caption(f"   ↳ {mt_name}")
    
    # Summary insights
    st.divider()
    st.markdown("### 💡 Key Insights")
    
    insights = []
    
    # Most pressing issue area
    if issue_tag_counts:
        top_issue = max(issue_tag_counts.items(), key=lambda x: x[1])
        insights.append(f"**{issue_tags.get(top_issue[0], {}).get('name', top_issue[0])}** is the most discussed issue area, appearing in {top_issue[1]} interviews")
    
    # Geographic concentration
    if location_counts and len(location_counts) > 1:
        top_location = max(location_counts.items(), key=lambda x: x[1])
        if top_location[1] / sum(location_counts.values()) > 0.3:
            insights.append(f"**{top_location[0]}** accounts for {top_location[1]/sum(location_counts.values())*100:.0f}% of interviews, showing geographic concentration")
    
    # Theme diversity
    if themes_per_interview:
        if avg_themes_per_interview > 5:
            insights.append(f"Interviews are **theme-rich** with an average of {avg_themes_per_interview:.1f} themes per interview")
        else:
            insights.append(f"Interviews are **focused** with an average of {avg_themes_per_interview:.1f} themes per interview")
    
    # Intensity patterns
    if intensity_counts and sum(intensity_counts.values()) > 0:
        high_intensity_pct = intensity_counts.get("high", 0) / sum(intensity_counts.values()) * 100
        if high_intensity_pct > 40:
            insights.append(f"**{high_intensity_pct:.0f}%** of themes are marked as high intensity, indicating urgent concerns")
    
    # Cross-cutting themes insight
    if cross_cutting:
        most_cross_cutting = cross_cutting[0]
        theme_name = most_cross_cutting[0]
        issue_count = len(most_cross_cutting[1])
        insights.append(f"**{theme_name}** is the most cross-cutting theme, appearing across {issue_count} different issue areas")
    
    for insight in insights:
        st.info(insight)

if __name__ == "__main__":
    main()