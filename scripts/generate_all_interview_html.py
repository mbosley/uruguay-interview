#!/usr/bin/env python3
"""
Generate HTML files for all interviews with annotations.
"""

import subprocess
from pathlib import Path
import json

def main():
    # Find all annotation files
    annotation_dir = Path("data/processed/annotations/production")
    annotation_files = sorted(annotation_dir.glob("*_final_annotation.json"))
    
    print(f"Found {len(annotation_files)} interviews to process")
    
    successful = []
    failed = []
    
    for annotation_file in annotation_files:
        # Extract interview ID
        interview_id = annotation_file.stem.split('_')[0]
        
        try:
            print(f"\nProcessing interview {interview_id}...")
            
            # Run the generator
            result = subprocess.run(
                ["python", "generate_interview_html_generic.py", interview_id],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ Successfully generated HTML for interview {interview_id}")
                successful.append(interview_id)
            else:
                print(f"✗ Failed to generate HTML for interview {interview_id}")
                print(f"  Error: {result.stderr}")
                failed.append(interview_id)
                
        except Exception as e:
            print(f"✗ Error processing interview {interview_id}: {str(e)}")
            failed.append(interview_id)
    
    # Summary
    print(f"\n{'='*50}")
    print(f"HTML Generation Summary")
    print(f"{'='*50}")
    print(f"Total interviews: {len(annotation_files)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed interviews: {', '.join(failed)}")
    
    # Create index file
    if successful:
        create_index_html(successful)

def create_index_html(interview_ids):
    """Create an index HTML file linking to all generated interviews."""
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Uruguay Interview Annotations - Index</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #FAFAF8;
            color: #1A1816;
        }
        h1 {
            margin-bottom: 2rem;
        }
        .interview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }
        .interview-card {
            background: white;
            border: 1px solid #E5E2DC;
            border-radius: 8px;
            padding: 1.5rem;
            text-decoration: none;
            color: inherit;
            transition: all 0.2s ease;
        }
        .interview-card:hover {
            border-color: #DC2626;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .interview-id {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #DC2626;
        }
        .interview-meta {
            font-size: 0.875rem;
            color: #4A453E;
        }
    </style>
</head>
<body>
    <h1>Uruguay Interview Annotations</h1>
    <p>Click on any interview to view the annotated conversation with all analysis dimensions.</p>
    
    <div class="interview-grid">
'''
    
    for interview_id in sorted(interview_ids):
        html_content += f'''
        <a href="interview_{interview_id}_annotated.html" class="interview-card">
            <div class="interview-id">Interview {interview_id}</div>
            <div class="interview-meta">View annotated conversation →</div>
        </a>
'''
    
    html_content += '''
    </div>
</body>
</html>
'''
    
    with open("interview_annotations_index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\nCreated index file: interview_annotations_index.html")

if __name__ == "__main__":
    main()