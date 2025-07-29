#!/usr/bin/env python3
"""
Create an interactive HTML report with real interview excerpts
"""

import json
import re
from pathlib import Path
from datetime import datetime

class InteractiveReportGenerator:
    def __init__(self, enriched_dir="../data/processed/enriched"):
        self.enriched_dir = Path(enriched_dir)
        self.interview_cache = {}
    
    def load_interview_turn(self, citation):
        """Load actual interview turn data"""
        try:
            interview_id, turn_num = citation.split(':')
            interview_id = interview_id.zfill(3)
            
            # Cache interviews as we load them
            if interview_id not in self.interview_cache:
                interview_file = self.enriched_dir / f"{interview_id}_enriched.json"
                if interview_file.exists():
                    with open(interview_file, 'r', encoding='utf-8') as f:
                        self.interview_cache[interview_id] = json.load(f)
                else:
                    return None
            
            # Find the specific turn
            interview = self.interview_cache.get(interview_id)
            if not interview:
                return None
            
            turn_id = f"{interview_id}:{int(turn_num):02d}"
            for turn in interview.get('turns', []):
                if turn['turn_id'] == turn_id:
                    return {
                        'turn_id': turn_id,
                        'speaker': turn['speaker'],
                        'text': turn['text'],
                        'themes': interview['indexes']['turn_by_id'][turn_id].get('themes', [])
                    }
            
            return None
        except Exception as e:
            print(f"Error loading turn {citation}: {e}")
            return None
    
    def create_tooltip_html(self, citation, turn_data):
        """Create rich tooltip with actual interview content"""
        if not turn_data:
            return f'''
            <div class="tooltip">
                <div class="tooltip-header">Turn {citation}</div>
                <div class="tooltip-text">[Data not available]</div>
            </div>
            '''
        
        # Truncate long quotes for tooltip
        text = turn_data['text']
        if len(text) > 300:
            text = text[:297] + '...'
        
        # Escape HTML
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        return f'''
        <div class="tooltip">
            <div class="tooltip-header">Turn {citation}</div>
            <div class="tooltip-speaker">Speaker: {turn_data['speaker']}</div>
            <div class="tooltip-text">{text}</div>
        </div>
        '''
    
    def process_citations(self, text):
        """Convert citations to interactive elements with real data"""
        pattern = r'[(`](\d{3}:\d{1,3})[)`]'
        
        def replace_citation(match):
            citation = match.group(1)
            turn_data = self.load_interview_turn(citation)
            tooltip = self.create_tooltip_html(citation, turn_data)
            return f'<span class="citation" data-citation="{citation}">{citation}{tooltip}</span>'
        
        return re.sub(pattern, replace_citation, text)
    
    def generate_report(self, results_file, output_file):
        """Generate the full interactive report"""
        # Load results
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Extract research question from the conversation
        research_question = "what do the interviews say about rural education?"
        for msg in results.get('full_conversation', []):
            if msg['role'] == 'user' and 'Research Question:' in msg['content']:
                match = re.search(r'Research Question: (.+?)\n', msg['content'])
                if match:
                    research_question = match.group(1)
                    break
        
        # Create enhanced HTML with modern design
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Report: {research_question}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1e40af;
            --secondary: #64748b;
            --accent: #f59e0b;
            --success: #10b981;
            --danger: #ef4444;
            --bg-light: #f8fafc;
            --bg-white: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border: #e2e8f0;
            --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background: var(--bg-light);
            margin: 0;
            padding: 0;
        }}
        
        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
            box-shadow: var(--shadow-lg);
        }}
        
        .header h1 {{
            margin: 0 0 1rem 0;
            font-size: 2.5rem;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }}
        
        .container {{
            max-width: 1000px;
            margin: -2rem auto 0;
            padding: 0 2rem 2rem;
            position: relative;
            z-index: 1;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}
        
        .stat-card {{
            background: var(--bg-white);
            padding: 1.5rem;
            border-radius: 0.75rem;
            box-shadow: var(--shadow);
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        .stat-icon {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 0.25rem;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}
        
        .section {{
            background: var(--bg-white);
            border-radius: 0.75rem;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow);
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border);
        }}
        
        .section-icon {{
            font-size: 1.75rem;
        }}
        
        .section h2 {{
            margin: 0;
            color: var(--text-primary);
            font-size: 1.75rem;
            font-weight: 600;
        }}
        
        .finding {{
            background: linear-gradient(to right, var(--bg-light) 0%, transparent 100%);
            border-left: 4px solid var(--primary);
            padding: 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0.5rem;
        }}
        
        .finding-header {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 0.75rem;
        }}
        
        .finding-content {{
            color: var(--text-secondary);
        }}
        
        .citation {{
            color: var(--primary);
            text-decoration: none;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            padding: 0.125rem 0.375rem;
            background: rgba(37, 99, 235, 0.1);
            border-radius: 0.25rem;
            cursor: pointer;
            position: relative;
            transition: all 0.2s;
            display: inline-block;
        }}
        
        .citation:hover {{
            background: rgba(37, 99, 235, 0.2);
            transform: translateY(-1px);
        }}
        
        .tooltip {{
            visibility: hidden;
            position: absolute;
            z-index: 1000;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(-0.5rem);
            background: var(--text-primary);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: var(--shadow-lg);
            width: 350px;
            max-width: 90vw;
            opacity: 0;
            transition: opacity 0.3s, transform 0.3s;
            pointer-events: none;
        }}
        
        .citation:hover .tooltip {{
            visibility: visible;
            opacity: 1;
            transform: translateX(-50%) translateY(-0.75rem);
        }}
        
        .tooltip::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: var(--text-primary) transparent transparent transparent;
        }}
        
        .tooltip-header {{
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 0.5rem;
            font-size: 0.875rem;
        }}
        
        .tooltip-speaker {{
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 0.5rem;
        }}
        
        .tooltip-text {{
            font-size: 0.875rem;
            line-height: 1.5;
            white-space: pre-wrap;
        }}
        
        .theme-card {{
            background: var(--bg-light);
            border-radius: 0.5rem;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid var(--border);
        }}
        
        .theme-header {{
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.75rem;
            font-size: 1.125rem;
        }}
        
        .theme-quote {{
            background: var(--bg-white);
            padding: 1rem;
            border-left: 3px solid var(--secondary);
            margin: 0.75rem 0;
            font-style: italic;
            color: var(--text-secondary);
            border-radius: 0.25rem;
        }}
        
        .journey-entry {{
            background: #fffbeb;
            border-left: 3px solid var(--accent);
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0.25rem;
            font-style: italic;
            color: #92400e;
        }}
        
        .journey-timestamp {{
            font-size: 0.75rem;
            color: #b45309;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        
        .narrative-section {{
            background: var(--bg-light);
            padding: 2rem;
            border-radius: 0.5rem;
            margin: 1.5rem 0;
            line-height: 1.8;
        }}
        
        .narrative-section p {{
            margin: 1rem 0;
            color: var(--text-secondary);
        }}
        
        .narrative-section p:first-child {{
            margin-top: 0;
        }}
        
        .methodology-note {{
            background: #f0f9ff;
            border-left: 3px solid #0284c7;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            color: #075985;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .container {{
                padding: 0 1rem 2rem;
            }}
            
            .section {{
                padding: 1.5rem;
            }}
            
            .tooltip {{
                width: 280px;
            }}
        }}
        
        @media print {{
            .tooltip {{
                display: none !important;
            }}
            
            .citation {{
                color: var(--primary);
                background: none;
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1>Rural Education in Uruguay: Voices from the Interior</h1>
        <p class="subtitle">{research_question}</p>
    </header>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">📚</div>
                <div class="stat-number">35</div>
                <div class="stat-label">Citizen Interviews</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🔍</div>
                <div class="stat-number">{len(results['tool_calls'])}</div>
                <div class="stat-label">Research Actions</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">💡</div>
                <div class="stat-number">4</div>
                <div class="stat-label">Key Findings</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🏫</div>
                <div class="stat-number">5</div>
                <div class="stat-label">Rural Education Voices</div>
            </div>
        </div>
"""
        
        # Parse and add content sections
        response = results['final_response']
        sections = self.parse_markdown_sections(response)
        
        # Add Key Findings
        html += self.generate_findings_section(sections.get('Key_Findings', ''))
        
        # Add Themes
        html += self.generate_themes_section(sections.get('Themes_Identified', ''))
        
        # Add Narrative
        html += self.generate_narrative_section(sections.get('Narrative Summary', ''))
        
        # Add Research Journey
        html += self.generate_journey_section(results)
        
        # Add Methodology
        html += self.generate_methodology_section(sections.get('TECHNICAL NOTES', ''))
        
        html += """
    </div>
    
    <script>
        // Enhanced interactivity
        document.addEventListener('DOMContentLoaded', function() {
            // Track citation hovers for analytics
            const citations = document.querySelectorAll('.citation');
            citations.forEach(citation => {
                citation.addEventListener('mouseenter', function() {
                    console.log('Citation viewed:', this.dataset.citation);
                });
            });
            
            // Smooth scroll for any internal links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                });
            });
        });
    </script>
</body>
</html>
"""
        
        # Write the report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Interactive report created: {output_file}")
        print(f"📊 Processed {len(self.interview_cache)} interviews")
        
    def parse_markdown_sections(self, markdown):
        """Parse markdown into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in markdown.split('\n'):
            if line.startswith('# '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[2:].strip()
                current_content = []
            elif line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def generate_findings_section(self, findings_text):
        """Generate the findings section with citations"""
        html = '''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">📌</span>
                <h2>Key Findings</h2>
            </div>
        '''
        
        # Parse findings
        finding_pattern = r'Finding_\d+:(.*?)(?=Finding_\d+:|$)'
        findings = re.findall(finding_pattern, findings_text, re.DOTALL)
        
        for i, finding in enumerate(findings, 1):
            lines = finding.strip().split('\n')
            statement = ""
            evidence = ""
            significance = ""
            
            for line in lines:
                if line.startswith('- Statement:'):
                    statement = line[12:].strip()
                elif line.startswith('- Evidence:'):
                    evidence = line[11:].strip()
                elif line.startswith('- Significance:'):
                    significance = line[15:].strip()
            
            html += f'''
            <div class="finding">
                <div class="finding-header">
                    <span>🔍</span>
                    <span>Finding {i}</span>
                </div>
                <div class="finding-content">
                    <p><strong>{statement}</strong></p>
                    <p>{self.process_citations(evidence)}</p>
                    <p style="color: var(--success); font-style: italic;">➔ {significance}</p>
                </div>
            </div>
            '''
        
        html += '</section>'
        return html
    
    def generate_themes_section(self, themes_text):
        """Generate themes section"""
        html = '''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">🎯</span>
                <h2>Major Themes</h2>
            </div>
        '''
        
        theme_pattern = r'Theme_\d+: (.*?)\n- Description: (.*?)\n- Example: (.*?)\n- Frequency: (.*?)(?=Theme_|$)'
        themes = re.findall(theme_pattern, themes_text, re.DOTALL)
        
        for theme_name, description, example, frequency in themes:
            html += f'''
            <div class="theme-card">
                <div class="theme-header">{theme_name.strip()}</div>
                <p>{description.strip()}</p>
                <div class="theme-quote">
                    {self.process_citations(example.strip())}
                </div>
                <p style="font-size: 0.875rem; color: var(--text-secondary);">
                    <strong>Frequency:</strong> {frequency.strip()}
                </p>
            </div>
            '''
        
        html += '</section>'
        return html
    
    def generate_narrative_section(self, narrative_text):
        """Generate narrative analysis section"""
        html = '''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">📖</span>
                <h2>Narrative Analysis</h2>
            </div>
            <div class="narrative-section">
        '''
        
        for paragraph in narrative_text.split('\n\n'):
            if paragraph.strip():
                html += f'<p>{self.process_citations(paragraph.strip())}</p>'
        
        html += '''
            </div>
        </section>
        '''
        return html
    
    def generate_journey_section(self, results):
        """Generate research journey section"""
        html = '''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">🗺️</span>
                <h2>Research Journey</h2>
            </div>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                How the understanding developed through {0} research actions:
            </p>
        '''.format(len(results['tool_calls']))
        
        # Show selected scratchpad entries
        scratchpad_entries = [tc for tc in results['tool_calls'] if tc['tool'] == 'scratchpad_append']
        
        for entry in scratchpad_entries[:4]:  # Show first 4 thoughtful moments
            timestamp = entry['timestamp'].split('T')[1].split('.')[0]
            note = entry['args']['note']
            
            html += f'''
            <div class="journey-entry">
                <div class="journey-timestamp">Research Note @ {timestamp}</div>
                {self.process_citations(note)}
            </div>
            '''
        
        html += '</section>'
        return html
    
    def generate_methodology_section(self, technical_text):
        """Generate methodology section"""
        html = '''
        <section class="section">
            <div class="section-header">
                <span class="section-icon">⚙️</span>
                <h2>Research Methodology</h2>
            </div>
        '''
        
        # Parse technical notes
        lines = technical_text.strip().split('\n')
        for line in lines:
            if line.startswith('- '):
                html += f'<p>• {line[2:]}</p>'
            elif line.strip():
                html += f'<div class="methodology-note">{line}</div>'
        
        html += '</section>'
        return html

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python create_interactive_report.py <results_json_file>")
        sys.exit(1)
    
    results_file = Path(sys.argv[1])
    output_file = results_file.with_suffix('.html')
    
    generator = InteractiveReportGenerator()
    generator.generate_report(results_file, output_file)