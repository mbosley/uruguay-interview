"""
Research-grade analytics module for enhanced dashboard
Statistical analysis, cross-tabulation, and research tools
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import chi2_contingency, pearsonr, spearmanr
from scipy.stats import mannwhitneyu, kruskal
import seaborn as sns
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional

class ResearchAnalytics:
    """Advanced analytics for qualitative research."""
    
    def __init__(self):
        self.significance_level = 0.05
    
    def create_crosstab_analysis(self, df: pd.DataFrame):
        """Interactive cross-tabulation analysis with statistical tests."""
        st.subheader("📊 Cross-Variable Analysis")
        st.markdown("*Explore relationships between variables with statistical significance testing*")
        
        # Variable selection
        categorical_vars = [
            'department', 'age_range', 'gender', 'locality_size',
            'dominant_frame', 'temporal_orientation', 'solution_orientation',
            'occupation_sector'
        ]
        
        numerical_vars = [
            'government_responsibility', 'individual_responsibility', 'structural_factors',
            'profile_confidence', 'narrative_confidence', 'duration_minutes',
            'avg_emotional_intensity', 'total_priorities'
        ]
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            primary_var = st.selectbox(
                "Primary Variable (Rows)",
                options=categorical_vars,
                index=0,
                help="Choose the main variable for analysis"
            )
        
        with col2:
            secondary_var = st.selectbox(
                "Secondary Variable (Columns)",
                options=[v for v in categorical_vars if v != primary_var],
                index=0,
                help="Choose the variable to cross-tabulate with"
            )
        
        with col3:
            analysis_type = st.selectbox(
                "Analysis Type",
                options=["Count", "Percentage", "Statistical Test"],
                index=0
            )
        
        if primary_var and secondary_var:
            self.show_crosstab_results(df, primary_var, secondary_var, analysis_type)
    
    def show_crosstab_results(self, df: pd.DataFrame, var1: str, var2: str, analysis_type: str):
        """Display cross-tabulation results with visualizations."""
        # Filter out missing values
        clean_df = df[[var1, var2]].dropna()
        
        if len(clean_df) == 0:
            st.warning("No data available for selected variables")
            return
        
        # Create cross-tabulation
        crosstab = pd.crosstab(clean_df[var1], clean_df[var2])
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"**Cross-tabulation: {var1} × {var2}**")
            
            if analysis_type == "Count":
                st.dataframe(crosstab, use_container_width=True)
                
            elif analysis_type == "Percentage":
                crosstab_pct = pd.crosstab(clean_df[var1], clean_df[var2], normalize='index') * 100
                st.dataframe(crosstab_pct.round(1), use_container_width=True)
                st.caption("Row percentages")
                
            elif analysis_type == "Statistical Test":
                self.perform_statistical_test(crosstab, var1, var2)
        
        with col2:
            # Visualization
            if analysis_type == "Percentage":
                crosstab_pct = pd.crosstab(clean_df[var1], clean_df[var2], normalize='index') * 100
                fig = px.imshow(
                    crosstab_pct.values,
                    x=crosstab_pct.columns,
                    y=crosstab_pct.index,
                    color_continuous_scale='Blues',
                    title=f"Heatmap: {var1} × {var2}",
                    labels=dict(color="Percentage")
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Stacked bar chart
                crosstab_pct = pd.crosstab(clean_df[var1], clean_df[var2], normalize='index') * 100
                fig = px.bar(
                    crosstab_pct,
                    title=f"Distribution: {var1} by {var2}",
                    labels={'value': 'Percentage', 'index': var1}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    def perform_statistical_test(self, crosstab: pd.DataFrame, var1: str, var2: str):
        """Perform chi-square test for independence."""
        try:
            chi2, p_value, dof, expected = chi2_contingency(crosstab)
            
            st.markdown("**Chi-square Test Results:**")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Chi-square", f"{chi2:.3f}")
            with col2:
                st.metric("p-value", f"{p_value:.3f}")
            with col3:
                st.metric("Degrees of Freedom", dof)
            
            # Interpretation
            if p_value < self.significance_level:
                st.success(f"✅ **Significant association** (p < {self.significance_level})")
                st.write(f"There is a statistically significant relationship between {var1} and {var2}")
            else:
                st.info(f"ℹ️ **No significant association** (p ≥ {self.significance_level})")
                st.write(f"No statistically significant relationship found between {var1} and {var2}")
            
            # Effect size (Cramér's V)
            n = crosstab.sum().sum()
            cramers_v = np.sqrt(chi2 / (n * (min(crosstab.shape) - 1)))
            st.metric("Cramér's V (Effect Size)", f"{cramers_v:.3f}")
            
            if cramers_v < 0.1:
                st.caption("Small effect size")
            elif cramers_v < 0.3:
                st.caption("Medium effect size")
            else:
                st.caption("Large effect size")
                
        except Exception as e:
            st.error(f"Statistical test failed: {str(e)}")
    
    def create_correlation_analysis(self, df: pd.DataFrame):
        """Advanced correlation analysis for numerical variables."""
        st.subheader("🔗 Correlation Analysis")
        st.markdown("*Explore relationships between numerical variables*")
        
        numerical_vars = [
            'government_responsibility', 'individual_responsibility', 'structural_factors',
            'profile_confidence', 'narrative_confidence', 'duration_minutes',
            'avg_emotional_intensity', 'total_priorities', 'national_priorities', 'local_priorities'
        ]
        
        # Filter to available numerical columns
        available_vars = [var for var in numerical_vars if var in df.columns and df[var].notna().sum() > 0]
        
        if len(available_vars) < 2:
            st.warning("Not enough numerical variables for correlation analysis")
            return
        
        # Correlation matrix
        corr_df = df[available_vars].corr()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Interactive correlation heatmap
            fig = px.imshow(
                corr_df.values,
                x=corr_df.columns,
                y=corr_df.index,
                color_continuous_scale='RdBu',
                color_continuous_midpoint=0,
                title="Correlation Matrix",
                labels=dict(color="Correlation"),
                zmin=-1, zmax=1
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Strong Correlations:**")
            
            # Find strong correlations
            strong_corr = []
            for i in range(len(corr_df.columns)):
                for j in range(i+1, len(corr_df.columns)):
                    corr_val = corr_df.iloc[i, j]
                    if abs(corr_val) > 0.5:  # Strong correlation threshold
                        strong_corr.append({
                            'var1': corr_df.columns[i],
                            'var2': corr_df.columns[j],
                            'correlation': corr_val
                        })
            
            if strong_corr:
                for corr_info in sorted(strong_corr, key=lambda x: abs(x['correlation']), reverse=True):
                    corr_val = corr_info['correlation']
                    color = "🟢" if corr_val > 0 else "🔴"
                    st.write(f"{color} {corr_info['var1']} ↔ {corr_info['var2']}: {corr_val:.3f}")
            else:
                st.info("No strong correlations found (|r| > 0.5)")
    
    def create_group_comparison_analysis(self, df: pd.DataFrame):
        """Compare groups across different variables."""
        st.subheader("👥 Group Comparison Analysis")
        st.markdown("*Compare groups using statistical tests*")
        
        categorical_vars = ['department', 'age_range', 'gender', 'dominant_frame', 'locality_size']
        numerical_vars = ['government_responsibility', 'individual_responsibility', 'structural_factors', 
                         'profile_confidence', 'narrative_confidence', 'avg_emotional_intensity']
        
        col1, col2 = st.columns(2)
        
        with col1:
            group_var = st.selectbox(
                "Grouping Variable",
                options=[var for var in categorical_vars if var in df.columns],
                help="Variable to create groups"
            )
        
        with col2:
            compare_var = st.selectbox(
                "Variable to Compare",
                options=[var for var in numerical_vars if var in df.columns],
                help="Numerical variable to compare across groups"
            )
        
        if group_var and compare_var:
            self.perform_group_comparison(df, group_var, compare_var)
    
    def perform_group_comparison(self, df: pd.DataFrame, group_var: str, compare_var: str):
        """Perform statistical comparison between groups."""
        # Clean data
        clean_df = df[[group_var, compare_var]].dropna()
        
        if len(clean_df) == 0:
            st.warning("No data available for comparison")
            return
        
        groups = clean_df.groupby(group_var)[compare_var].apply(list)
        group_names = list(groups.index)
        group_values = list(groups.values)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Box plot comparison
            fig = px.box(
                clean_df,
                x=group_var,
                y=compare_var,
                title=f"{compare_var} by {group_var}",
                points="outliers"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Group Statistics:**")
            
            # Summary statistics
            summary_stats = clean_df.groupby(group_var)[compare_var].agg(['count', 'mean', 'std']).round(3)
            st.dataframe(summary_stats, use_container_width=True)
            
            # Statistical test
            if len(group_values) == 2:
                # Two groups: Mann-Whitney U test
                stat, p_value = mannwhitneyu(group_values[0], group_values[1], alternative='two-sided')
                st.markdown("**Mann-Whitney U Test:**")
                st.metric("p-value", f"{p_value:.3f}")
                
            elif len(group_values) > 2:
                # Multiple groups: Kruskal-Wallis test
                stat, p_value = kruskal(*group_values)
                st.markdown("**Kruskal-Wallis Test:**")
                st.metric("p-value", f"{p_value:.3f}")
            
            # Interpretation
            if p_value < self.significance_level:
                st.success("✅ **Significant difference**")
                st.write("Groups differ significantly")
            else:
                st.info("ℹ️ **No significant difference**")
                st.write("No significant difference between groups")
    
    def create_confidence_analysis(self, df: pd.DataFrame):
        """Analyze annotation confidence patterns."""
        st.subheader("🎯 Confidence Analysis")
        st.markdown("*Quality assessment and confidence patterns*")
        
        confidence_vars = ['profile_confidence', 'narrative_confidence']
        available_confidence = [var for var in confidence_vars if var in df.columns and df[var].notna().sum() > 0]
        
        if not available_confidence:
            st.warning("No confidence data available")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Confidence distribution
            fig = go.Figure()
            
            for var in available_confidence:
                values = df[var].dropna()
                fig.add_trace(go.Histogram(
                    x=values,
                    name=var.replace('_', ' ').title(),
                    opacity=0.7,
                    nbinsx=20
                ))
            
            fig.update_layout(
                title="Confidence Score Distribution",
                xaxis_title="Confidence Score",
                yaxis_title="Count",
                barmode='overlay'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Confidence statistics
            st.markdown("**Confidence Statistics:**")
            
            for var in available_confidence:
                values = df[var].dropna()
                if len(values) > 0:
                    st.markdown(f"**{var.replace('_', ' ').title()}:**")
                    st.write(f"Mean: {values.mean():.3f}")
                    st.write(f"Median: {values.median():.3f}")
                    st.write(f"Std Dev: {values.std():.3f}")
                    
                    # Quality categories
                    high_conf = (values >= 0.8).sum()
                    med_conf = ((values >= 0.6) & (values < 0.8)).sum()
                    low_conf = (values < 0.6).sum()
                    
                    st.write(f"High confidence (≥0.8): {high_conf} ({high_conf/len(values)*100:.1f}%)")
                    st.write(f"Medium confidence (0.6-0.8): {med_conf} ({med_conf/len(values)*100:.1f}%)")
                    st.write(f"Low confidence (<0.6): {low_conf} ({low_conf/len(values)*100:.1f}%)")
                    st.markdown("---")
    
    def create_pattern_discovery(self, df: pd.DataFrame):
        """Advanced pattern discovery and insights."""
        st.subheader("🔍 Pattern Discovery")
        st.markdown("*Automated insights and pattern detection*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Dominant Patterns:**")
            
            # Most common combinations
            if 'dominant_frame' in df.columns and 'age_range' in df.columns:
                frame_age = df.groupby(['dominant_frame', 'age_range']).size().sort_values(ascending=False).head(5)
                st.write("Top Frame-Age combinations:")
                for (frame, age), count in frame_age.items():
                    st.write(f"• {frame} + {age}: {count} interviews")
            
            st.markdown("---")
            
            # Department patterns
            if 'department' in df.columns and 'dominant_frame' in df.columns:
                dept_frame = pd.crosstab(df['department'], df['dominant_frame'], normalize='index') * 100
                st.write("Department narrative patterns:")
                for dept in dept_frame.index:
                    dominant_frame = dept_frame.loc[dept].idxmax()
                    percentage = dept_frame.loc[dept, dominant_frame]
                    st.write(f"• {dept}: {dominant_frame} ({percentage:.1f}%)")
        
        with col2:
            st.markdown("**Outlier Detection:**")
            
            # Find unusual cases
            outliers = []
            
            # High individual responsibility (unusual)
            if 'individual_responsibility' in df.columns:
                high_individual = df[df['individual_responsibility'] > 0.7]
                if len(high_individual) > 0:
                    outliers.append(f"High individual responsibility: {len(high_individual)} cases")
            
            # Low government responsibility (unusual given our data)
            if 'government_responsibility' in df.columns:
                low_government = df[df['government_responsibility'] < 0.4]
                if len(low_government) > 0:
                    outliers.append(f"Low government responsibility: {len(low_government)} cases")
            
            # Progress frame (minority)
            if 'dominant_frame' in df.columns:
                progress_frame = df[df['dominant_frame'] == 'progress']
                if len(progress_frame) > 0:
                    pct = len(progress_frame) / len(df) * 100
                    outliers.append(f"Progress narrative: {len(progress_frame)} cases ({pct:.1f}%)")
            
            if outliers:
                for outlier in outliers:
                    st.write(f"🔎 {outlier}")
            else:
                st.info("No significant outliers detected")


def show_research_analytics_page(df: pd.DataFrame):
    """Main function to display research analytics page."""
    st.title("🔬 Research Analytics")
    st.markdown("*Advanced statistical analysis and pattern discovery*")
    
    analytics = ResearchAnalytics()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Cross-Analysis", 
        "🔗 Correlations", 
        "👥 Group Comparison",
        "🎯 Quality Analysis",
        "🔍 Pattern Discovery"
    ])
    
    with tab1:
        analytics.create_crosstab_analysis(df)
    
    with tab2:
        analytics.create_correlation_analysis(df)
    
    with tab3:
        analytics.create_group_comparison_analysis(df)
    
    with tab4:
        analytics.create_confidence_analysis(df)
    
    with tab5:
        analytics.create_pattern_discovery(df)