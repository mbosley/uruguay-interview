#!/usr/bin/env python3
"""
Create an interactive HTML report from research results
"""

import json
import re
from pathlib import Path
from datetime import datetime

def extract_citations(text):
    """Extract all citations from text and return with their context"""
    # Pattern to match citations like (068:151) or (`068:151`)
    pattern = r'[(`](\d{3}:\d{1,3})[)`]'
    citations = []
    
    for match in re.finditer(pattern, text):
        citation = match.group(1)
        # Get surrounding context (50 chars before and after)
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end]
        citations.append({
            'citation': citation,
            'context': context,
            'position': match.start()
        })
    
    return citations

def create_html_report(results_file, output_file):
    """Create interactive HTML report from research results"""
    
    # Load results
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Parse the markdown response
    response = results['final_response']
    
    # Extract sections
    sections = {}
    current_section = None
    current_content = []
    
    for line in response.split('\n'):
        if line.startswith('# '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line[2:]
            current_content = []
        elif line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line[3:]
            current_content = []
        else:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rural Education in Uruguay - Research Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        
        .report-container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
        }}
        
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        
        .metadata {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
            font-size: 0.9em;
        }}
        
        .finding {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 5px 5px 0;
        }}
        
        .finding-statement {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .finding-evidence {{
            color: #555;
            margin: 10px 0;
        }}
        
        .finding-significance {{
            color: #16a085;
            font-style: italic;
            margin-top: 10px;
        }}
        
        .citation {{
            color: #3498db;
            text-decoration: none;
            border-bottom: 1px dotted #3498db;
            cursor: pointer;
            font-family: monospace;
            font-size: 0.95em;
            position: relative;
            white-space: nowrap;
        }}
        
        .citation:hover {{
            background: #e3f2fd;
            border-radius: 3px;
            padding: 0 2px;
        }}
        
        .tooltip {{
            visibility: hidden;
            width: 400px;
            background-color: #2c3e50;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 15px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -200px;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 0.9em;
            line-height: 1.5;
        }}
        
        .tooltip::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #2c3e50 transparent transparent transparent;
        }}
        
        .citation:hover .tooltip {{
            visibility: visible;
            opacity: 1;
        }}
        
        .tooltip-header {{
            font-weight: bold;
            color: #3498db;
            margin-bottom: 8px;
            padding-bottom: 5px;
            border-bottom: 1px solid #34495e;
        }}
        
        .tooltip-speaker {{
            color: #ecf0f1;
            font-size: 0.85em;
            margin-bottom: 5px;
        }}
        
        .tooltip-text {{
            color: #ecf0f1;
            white-space: pre-wrap;
        }}
        
        .theme-card {{
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        
        .theme-name {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .theme-description {{
            color: #555;
            margin: 10px 0;
        }}
        
        .theme-example {{
            background: #f5f5f5;
            padding: 10px 15px;
            border-left: 3px solid #95a5a6;
            margin: 10px 0;
            font-style: italic;
            color: #666;
        }}
        
        .narrative {{
            background: #fafafa;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
            line-height: 1.8;
            color: #444;
        }}
        
        .research-journey {{
            background: #fffef0;
            border: 1px solid #f0e68c;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
        }}
        
        .journey-header {{
            font-weight: bold;
            color: #8b7500;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .journey-icon {{
            font-size: 1.5em;
        }}
        
        .scratchpad-entry {{
            background: #fff;
            border-left: 3px solid #f0e68c;
            padding: 15px;
            margin: 10px 0;
            font-family: Georgia, serif;
            color: #555;
            font-style: italic;
        }}
        
        .nav-sidebar {{
            position: fixed;
            left: 20px;
            top: 50%;
            transform: translateY(-50%);
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 200px;
        }}
        
        .nav-link {{
            display: block;
            color: #3498db;
            text-decoration: none;
            padding: 5px 0;
            font-size: 0.9em;
        }}
        
        .nav-link:hover {{
            color: #2c3e50;
            text-decoration: underline;
        }}
        
        @media (max-width: 1200px) {{
            .nav-sidebar {{
                display: none;
            }}
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: #3498db;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="nav-sidebar">
        <h4>Navigate</h4>
        <a href="#findings" class="nav-link">Key Findings</a>
        <a href="#themes" class="nav-link">Themes</a>
        <a href="#narrative" class="nav-link">Narrative</a>
        <a href="#journey" class="nav-link">Research Journey</a>
        <a href="#technical" class="nav-link">Technical Notes</a>
    </div>

    <div class="report-container">
        <h1>🌾 Rural Education in Uruguay: A Crisis of Abandonment</h1>
        
        <div class="metadata">
            <strong>Research Date:</strong> {datetime.now().strftime('%B %d, %Y')}<br>
            <strong>Corpus:</strong> 35 citizen consultation interviews (May 28-29, 2025)<br>
            <strong>Research Question:</strong> What do the interviews say about rural education?<br>
            <strong>Key Finding:</strong> Rural education faces systematic abandonment rather than mere underfunding
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">35</div>
                <div class="stat-label">Interviews Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">5</div>
                <div class="stat-label">Primary Rural Education Interviews</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">4</div>
                <div class="stat-label">Major Themes Identified</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">15</div>
                <div class="stat-label">Research Iterations</div>
            </div>
        </div>
"""
    
    # Add structured findings
    html += '<h2 id="findings">Key Findings</h2>'
    
    # Process findings from the response
    findings_text = sections.get('Key_Findings', '')
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
            <div class="finding-statement">Finding {i}: {statement}</div>
            <div class="finding-evidence"><strong>Evidence:</strong> {process_citations(evidence)}</div>
            <div class="finding-significance"><strong>Significance:</strong> {significance}</div>
        </div>
        '''
    
    # Add themes section
    html += '<h2 id="themes">Themes Identified</h2>'
    themes_text = sections.get('Themes_Identified', '')
    theme_pattern = r'Theme_\d+: (.*?)\n- Description: (.*?)\n- Example: (.*?)\n- Frequency: (.*?)(?=Theme_|$)'
    themes = re.findall(theme_pattern, themes_text, re.DOTALL)
    
    for theme_name, description, example, frequency in themes:
        html += f'''
        <div class="theme-card">
            <div class="theme-name">{theme_name.strip()}</div>
            <div class="theme-description">{description.strip()}</div>
            <div class="theme-example">{process_citations(example.strip())}</div>
            <div style="color: #7f8c8d; font-size: 0.9em;"><strong>Frequency:</strong> {frequency.strip()}</div>
        </div>
        '''
    
    # Add narrative section
    html += '<h2 id="narrative">Narrative Analysis</h2>'
    html += '<div class="narrative">'
    narrative = sections.get('Narrative Summary', '')
    for paragraph in narrative.split('\n\n'):
        if paragraph.strip():
            html += f'<p>{process_citations(paragraph.strip())}</p>'
    html += '</div>'
    
    # Add research journey section
    html += '''
    <h2 id="journey">Research Journey</h2>
    <div class="research-journey">
        <div class="journey-header">
            <span class="journey-icon">🔍</span>
            <span>How this understanding developed</span>
        </div>
    '''
    
    # Extract some scratchpad entries from the tool calls
    for tool_call in results['tool_calls'][:5]:  # Show first 5 thoughtful moments
        if tool_call['tool'] == 'scratchpad_append':
            note = tool_call['args']['note']
            html += f'<div class="scratchpad-entry">{process_citations(note)}</div>'
    
    html += '</div>'
    
    # Add technical notes
    html += '<h2 id="technical">Technical Notes</h2>'
    html += '<div style="background: #f5f5f5; padding: 20px; border-radius: 8px; font-size: 0.9em;">'
    technical = sections.get('TECHNICAL NOTES', '')
    html += f'<pre style="white-space: pre-wrap;">{technical}</pre>'
    html += '</div>'
    
    html += '''
    </div>
    
    <script>
        // Add smooth scrolling for navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
    </script>
</body>
</html>
'''
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML report created: {output_file}")

def process_citations(text):
    """Convert citations to interactive links with tooltips"""
    # For now, just make them styled - in real implementation, would load actual turn data
    pattern = r'[(`](\d{3}:\d{1,3})[)`]'
    
    def replace_citation(match):
        citation = match.group(1)
        interview_id, turn_num = citation.split(':')
        
        # Mock tooltip content - in real implementation, would load from data
        tooltip_content = f'''
        <div class="tooltip">
            <div class="tooltip-header">Turn {citation}</div>
            <div class="tooltip-speaker">Speaker: [Would load from data]</div>
            <div class="tooltip-text">[Full quote would appear here on hover - this would be loaded from the enriched interview files]</div>
        </div>
        '''
        
        return f'<span class="citation">{citation}{tooltip_content}</span>'
    
    return re.sub(pattern, replace_citation, text)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python create_html_report.py <results_json_file>")
        sys.exit(1)
    
    results_file = Path(sys.argv[1])
    output_file = results_file.with_suffix('.html')
    
    create_html_report(results_file, output_file)