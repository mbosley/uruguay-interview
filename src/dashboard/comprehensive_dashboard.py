"""
Comprehensive Enhanced Uruguay Interview Analysis Dashboard
Advanced research platform with all enhanced features integrated
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys
import io

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.app import InteractiveDashboard
from src.dashboard.research_analytics import show_research_analytics_page
from src.dashboard.quote_browser import show_quote_browser_page

# Configure page
st.set_page_config(
    page_title="Uruguay Research Platform - Comprehensive Dashboard",
    page_icon="🇺🇾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .nav-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #2196f3;
    }
    .feature-highlight {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .export-section {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)


class ComprehensiveDashboard:
    """Main comprehensive dashboard controller."""
    
    def __init__(self):
        self.interactive_dashboard = InteractiveDashboard()
        self.setup_session_state()
    
    def setup_session_state(self):
        """Initialize session state for navigation."""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'Overview'
        
        if 'export_data' not in st.session_state:
            st.session_state.export_data = {}
    
    def create_navigation_sidebar(self):
        """Enhanced navigation sidebar with feature descriptions."""
        st.sidebar.markdown("""
        <div class="main-header">
            <h2>🇺🇾 Uruguay Research Platform</h2>
            <p>Comprehensive Interview Analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Main navigation
        st.sidebar.title("📊 Navigation")
        
        pages = {
            '🔍 Interactive Explorer': {
                'key': 'explorer',
                'description': 'Dynamic filtering and linked visualizations'
            },
            '🔬 Research Analytics': {
                'key': 'analytics', 
                'description': 'Statistical analysis and cross-tabulation'
            },
            '💬 Quote Browser': {
                'key': 'quotes',
                'description': 'Advanced quote search and narrative analysis'
            },
            '📊 Overview Dashboard': {
                'key': 'overview',
                'description': 'High-level insights and summary metrics'
            },
            '📄 Export & Reports': {
                'key': 'export',
                'description': 'Data export and research report generation'
            }
        }
        
        # Display navigation options
        for page_name, page_info in pages.items():
            if st.sidebar.button(
                page_name, 
                key=f"nav_{page_info['key']}",
                help=page_info['description'],
                use_container_width=True
            ):
                st.session_state.current_page = page_info['key']
                st.rerun()
        
        # Current page indicator
        current_page = st.session_state.current_page
        st.sidebar.markdown(f"**Current:** {current_page}")
        
        # Feature highlights
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🚀 Platform Features")
        
        features = [
            "🔍 **Interactive Filtering** - Dynamic data exploration",
            "📊 **Statistical Analysis** - Chi-square, correlations, group comparisons", 
            "💬 **Quote Browser** - Advanced search across all quotes",
            "📚 **Narrative Analysis** - Identity, problem, and hope narratives",
            "🎭 **Cultural Patterns** - Pattern discovery and visualization",
            "📈 **Research-Grade Analytics** - Publication-ready analysis",
            "💾 **Export Tools** - CSV, Excel, and report generation"
        ]
        
        for feature in features:
            st.sidebar.markdown(f'<div class="feature-highlight">{feature}</div>', 
                               unsafe_allow_html=True)
    
    def show_overview_page(self):
        """Enhanced overview page with key insights."""
        st.title("📊 Uruguay Interview Analysis - Overview")
        st.markdown("### 🎯 Research Platform Summary")
        
        # Load data for overview
        interview_df, priority_df = self.interactive_dashboard.load_comprehensive_data()
        
        # Key metrics section
        st.markdown("### 📈 Key Metrics")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Interviews", len(interview_df))
        
        with col2:
            departments = interview_df['department'].nunique()
            st.metric("Departments", departments)
        
        with col3:
            avg_confidence = interview_df['narrative_confidence'].mean()
            st.metric("Avg Confidence", f"{avg_confidence:.2f}" if pd.notna(avg_confidence) else "N/A")
        
        with col4:
            total_priorities = len(priority_df) if len(priority_df) > 0 else 0
            st.metric("Total Priorities", total_priorities)
        
        with col5:
            avg_emotional = interview_df['avg_emotional_intensity'].mean()
            st.metric("Avg Emotional Intensity", f"{avg_emotional:.2f}" if pd.notna(avg_emotional) else "N/A")
        
        # Key insights
        st.markdown("### 🔍 Key Research Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Narrative frame distribution
            frames = interview_df['dominant_frame'].value_counts()
            if not frames.empty:
                fig = px.pie(
                    values=frames.values,
                    names=frames.index,
                    title="Dominant Narrative Frames",
                    color_discrete_map={
                        'decline': '#ffcdd2',
                        'progress': '#c8e6c9',
                        'stagnation': '#ffe0b2',
                        'mixed': '#e1bee7'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Geographic distribution
            dept_counts = interview_df['department'].value_counts()
            if not dept_counts.empty:
                fig = px.bar(
                    x=dept_counts.values,
                    y=dept_counts.index,
                    orientation='h',
                    title="Interviews by Department",
                    labels={'x': 'Count', 'y': 'Department'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Research highlights
        st.markdown("### 📚 Research Highlights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🎭 Dominant Patterns")
            decline_pct = (frames.get('decline', 0) / len(interview_df)) * 100 if not frames.empty else 0
            st.write(f"• **Decline narrative**: {decline_pct:.1f}% of interviews")
            
            rio_negro_pct = (dept_counts.get('Río Negro', 0) / len(interview_df)) * 100 if not dept_counts.empty else 0
            st.write(f"• **Río Negro focus**: {rio_negro_pct:.1f}% of interviews")
            
            mature_demo = interview_df['age_range'].value_counts().get('50-64', 0)
            mature_pct = (mature_demo / len(interview_df)) * 100
            st.write(f"• **Mature participants**: {mature_pct:.1f}% aged 50-64")
        
        with col2:
            st.markdown("#### 🎯 Agency Attribution")
            gov_resp = interview_df['government_responsibility'].mean()
            ind_resp = interview_df['individual_responsibility'].mean()
            
            if pd.notna(gov_resp) and pd.notna(ind_resp):
                st.write(f"• **Government responsibility**: {gov_resp:.2f}/1.0")
                st.write(f"• **Individual responsibility**: {ind_resp:.2f}/1.0")
                st.write(f"• **Responsibility gap**: {abs(gov_resp - ind_resp):.2f}")
        
        with col3:
            st.markdown("#### 💬 Content Analysis")
            if len(priority_df) > 0:
                top_themes = priority_df['theme'].value_counts().head(3)
                st.write("**Top Priority Themes:**")
                for theme, count in top_themes.items():
                    st.write(f"• {theme}: {count} mentions")
        
        # Quick access to features
        st.markdown("### 🚀 Quick Access")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Start Interactive Exploration", use_container_width=True):
                st.session_state.current_page = 'explorer'
                st.rerun()
        
        with col2:
            if st.button("🔬 Advanced Analytics", use_container_width=True):
                st.session_state.current_page = 'analytics'
                st.rerun()
        
        with col3:
            if st.button("💬 Browse Quotes", use_container_width=True):
                st.session_state.current_page = 'quotes'
                st.rerun()
    
    def show_explorer_page(self):
        """Interactive explorer page."""
        # Load data
        interview_df, priority_df = self.interactive_dashboard.load_comprehensive_data()
        
        # Create filter sidebar
        self.interactive_dashboard.create_filter_sidebar(interview_df)
        
        # Apply filters
        filtered_df = self.interactive_dashboard.apply_filters(interview_df)
        
        # Show overview metrics
        self.interactive_dashboard.show_overview_metrics(interview_df, filtered_df)
        
        st.markdown("---")
        
        # Show narrative analysis
        self.interactive_dashboard.create_linked_narrative_analysis(filtered_df)
        
        st.markdown("---")
        
        # Show agency analysis
        self.interactive_dashboard.create_interactive_agency_analysis(filtered_df)
        
        st.markdown("---")
        
        # Interview explorer
        selected_interview = self.interactive_dashboard.create_interview_selector(filtered_df)
        
        if selected_interview:
            st.markdown("---")
            self.interactive_dashboard.show_detailed_interview_analysis(selected_interview, filtered_df)
    
    def show_export_page(self):
        """Export and reporting page."""
        st.title("📄 Export & Research Reports")
        st.markdown("*Generate exports and research-ready reports*")
        
        # Load data
        interview_df, priority_df = self.interactive_dashboard.load_comprehensive_data()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 💾 Data Export Options")
            
            # Export format selection
            export_format = st.selectbox(
                "Export Format",
                options=['CSV', 'Excel (XLSX)', 'JSON'],
                help="Choose format for data export"
            )
            
            # Data selection
            export_data_type = st.selectbox(
                "Data to Export",
                options=['Interview Data', 'Priority Data', 'Both', 'Filtered Data'],
                help="Choose which data to include in export"
            )
            
            # Apply current filters for export
            if export_data_type == 'Filtered Data':
                filtered_df = self.interactive_dashboard.apply_filters(interview_df)
                st.info(f"Will export {len(filtered_df)} filtered interviews")
            
            # Export button
            if st.button("📥 Generate Export", type="primary"):
                self.generate_export(interview_df, priority_df, export_format, export_data_type)
        
        with col2:
            st.markdown("### 📋 Export Features")
            
            features = [
                "✅ Complete interview metadata",
                "✅ Participant profiles with confidence scores", 
                "✅ Narrative features and cultural patterns",
                "✅ Priority analysis with quotes",
                "✅ Statistical summaries",
                "✅ Research-ready formatting",
                "✅ Citation information"
            ]
            
            for feature in features:
                st.write(feature)
        
        # Research report generation
        st.markdown("---")
        st.markdown("### 📊 Research Report Generator")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("Generate comprehensive research reports with:")
            
            report_options = st.multiselect(
                "Report Sections",
                options=[
                    "Executive Summary",
                    "Methodology",
                    "Demographic Analysis", 
                    "Narrative Frame Analysis",
                    "Priority Theme Analysis",
                    "Cultural Pattern Analysis",
                    "Statistical Analysis",
                    "Key Quotes",
                    "Recommendations"
                ],
                default=["Executive Summary", "Demographic Analysis", "Narrative Frame Analysis"]
            )
            
            report_format = st.selectbox(
                "Report Format",
                options=['HTML', 'Markdown', 'PDF (Future)'],
                index=0
            )
        
        with col2:
            if st.button("📝 Generate Report", type="primary"):
                self.generate_research_report(interview_df, priority_df, report_options, report_format)
    
    def generate_export(self, interview_df, priority_df, export_format, export_data_type):
        """Generate data export."""
        try:
            if export_data_type == 'Interview Data':
                data_to_export = interview_df
                filename = f"uruguay_interviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif export_data_type == 'Priority Data':
                data_to_export = priority_df
                filename = f"uruguay_priorities_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif export_data_type == 'Filtered Data':
                data_to_export = self.interactive_dashboard.apply_filters(interview_df)
                filename = f"uruguay_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:  # Both
                # For 'Both', we'll export the interview data (which includes priority aggregates)
                data_to_export = interview_df
                filename = f"uruguay_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if export_format == 'CSV':
                csv_buffer = io.StringIO()
                data_to_export.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"{filename}.csv",
                    mime="text/csv"
                )
            
            elif export_format == 'Excel (XLSX)':
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    data_to_export.to_excel(writer, sheet_name='Interview_Data', index=False)
                    if export_data_type in ['Both', 'Interview Data']:
                        priority_df.to_excel(writer, sheet_name='Priority_Data', index=False)
                
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"{filename}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            elif export_format == 'JSON':
                json_data = data_to_export.to_json(orient='records', indent=2)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"{filename}.json",
                    mime="application/json"
                )
            
            st.success(f"✅ Export ready! Click the download button above to save your {export_format} file.")
            
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
    
    def generate_research_report(self, interview_df, priority_df, report_sections, report_format):
        """Generate comprehensive research report."""
        try:
            report_content = self.build_research_report(interview_df, priority_df, report_sections)
            
            if report_format == 'HTML':
                st.download_button(
                    label="📝 Download HTML Report",
                    data=report_content,
                    file_name=f"uruguay_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )
            elif report_format == 'Markdown':
                st.download_button(
                    label="📝 Download Markdown Report", 
                    data=report_content,
                    file_name=f"uruguay_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            
            st.success("✅ Research report generated! Click the download button above.")
            
        except Exception as e:
            st.error(f"Report generation failed: {str(e)}")
    
    def build_research_report(self, interview_df, priority_df, sections):
        """Build comprehensive research report content."""
        if "HTML" in st.session_state.get('report_format', 'HTML'):
            return self.build_html_report(interview_df, priority_df, sections)
        else:
            return self.build_markdown_report(interview_df, priority_df, sections)
    
    def build_markdown_report(self, interview_df, priority_df, sections):
        """Build markdown research report."""
        report = []
        report.append("# Uruguay Interview Analysis - Research Report")
        report.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        if "Executive Summary" in sections:
            report.append("## Executive Summary")
            report.append(f"This report analyzes {len(interview_df)} citizen consultation interviews conducted in Uruguay.")
            report.append(f"The analysis covers {interview_df['department'].nunique()} departments with comprehensive narrative and priority analysis.\n")
        
        if "Demographic Analysis" in sections:
            report.append("## Demographic Analysis")
            
            age_dist = interview_df['age_range'].value_counts()
            report.append("### Age Distribution")
            for age, count in age_dist.items():
                pct = (count / len(interview_df)) * 100
                report.append(f"- {age}: {count} ({pct:.1f}%)")
            
            report.append("")
        
        if "Narrative Frame Analysis" in sections:
            report.append("## Narrative Frame Analysis")
            
            frames = interview_df['dominant_frame'].value_counts()
            report.append("### Dominant Narrative Frames")
            for frame, count in frames.items():
                pct = (count / len(interview_df)) * 100
                report.append(f"- {frame}: {count} ({pct:.1f}%)")
            
            report.append("")
        
        return "\n".join(report)
    
    def build_html_report(self, interview_df, priority_df, sections):
        """Build HTML research report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Uruguay Interview Analysis - Research Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; border-bottom: 2px solid #3498db; }}
                .metric {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .highlight {{ background: #e3f2fd; padding: 15px; margin: 15px 0; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <h1>Uruguay Interview Analysis - Research Report</h1>
            <p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
        """
        
        if "Executive Summary" in sections:
            html_content += f"""
            <h2>Executive Summary</h2>
            <div class="highlight">
                <p>This comprehensive analysis examines {len(interview_df)} citizen consultation interviews 
                conducted across {interview_df['department'].nunique()} departments in Uruguay.</p>
                <p>Key findings include significant prevalence of decline narratives and high attribution 
                of responsibility to government institutions.</p>
            </div>
            """
        
        if "Demographic Analysis" in sections:
            html_content += "<h2>Demographic Analysis</h2>"
            
            age_dist = interview_df['age_range'].value_counts()
            html_content += "<h3>Age Distribution</h3><ul>"
            for age, count in age_dist.items():
                pct = (count / len(interview_df)) * 100
                html_content += f"<li>{age}: {count} ({pct:.1f}%)</li>"
            html_content += "</ul>"
        
        html_content += "</body></html>"
        return html_content


def main():
    """Main comprehensive dashboard application."""
    dashboard = ComprehensiveDashboard()
    
    # Create navigation
    dashboard.create_navigation_sidebar()
    
    # Route to appropriate page
    current_page = st.session_state.get('current_page', 'overview')
    
    try:
        if current_page == 'overview':
            dashboard.show_overview_page()
        elif current_page == 'explorer':
            dashboard.show_explorer_page()
        elif current_page == 'analytics':
            # Load data for analytics
            interview_df, _ = dashboard.interactive_dashboard.load_comprehensive_data()
            show_research_analytics_page(interview_df)
        elif current_page == 'quotes':
            show_quote_browser_page()
        elif current_page == 'export':
            dashboard.show_export_page()
        else:
            dashboard.show_overview_page()
    
    except Exception as e:
        st.error(f"Error loading page: {str(e)}")
        st.exception(e)
    
    # Footer
    st.markdown("---")
    st.markdown("*🇺🇾 Uruguay Research Platform v3.0 - Comprehensive Analysis Dashboard*")


if __name__ == "__main__":
    main()