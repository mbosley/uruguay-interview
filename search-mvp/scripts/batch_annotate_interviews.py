#!/usr/bin/env python3
"""
Batch annotation script for Uruguay interviews
Model-agnostic: supports Kimi, OpenAI, Gemini, etc.
"""

import json
import os
import sys
import time
import yaml
from pathlib import Path
from datetime import datetime
import argparse
import logging
from dotenv import load_dotenv

# Add src to path
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)
from llm.providers import create_provider

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InterviewAnnotator:
    """Batch annotation processor for interview corpus"""
    
    def __init__(self, output_dir=None, provider_type=None, model=None):
        self.project_root = Path(__file__).parent.parent.parent
        self.structured_dir = self.project_root / "data" / "processed" / "structured"
        self.guidelines_path = Path(__file__).parent.parent / "prompts" / "interview_annotation_prompt.md"
        
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.project_root / "data" / "processed" / "annotations" / "searchable"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize LLM provider
        self.provider = self._init_provider(provider_type, model)
        
        # Track progress
        self.processed = []
        self.failed = []
        self.skipped = []
    
    def _load_config(self):
        """Load configuration from config.yaml"""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default config
            return {
                'models': {
                    'enrichment': {
                        'provider': 'kimi',
                        'model': 'kimi-k2-0711-preview'
                    }
                },
                'processing': {
                    'temperature': 0.7
                }
            }
    
    def _init_provider(self, provider_type=None, model=None):
        """Initialize LLM provider based on config or parameters"""
        if provider_type and model:
            # Use command line parameters
            return create_provider(provider_type, model)
        else:
            # Use config
            enrichment_config = self.config['models']['enrichment']
            return create_provider(
                enrichment_config['provider'],
                enrichment_config['model']
            )
    
    def load_guidelines(self):
        """Load annotation guidelines"""
        if not self.guidelines_path.exists():
            raise FileNotFoundError(f"Guidelines not found at {self.guidelines_path}")
        
        with open(self.guidelines_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_interview_files(self):
        """Get list of interview files to process"""
        files = list(self.structured_dir.glob("[0-9]*.json"))
        return sorted(files, key=lambda f: f.stem)
    
    def check_if_processed(self, interview_id):
        """Check if interview already has annotation"""
        output_file = self.output_dir / f"{interview_id}_annotation.json"
        return output_file.exists()
    
    def create_annotation_prompt(self, interview_data, guidelines):
        """Create the annotation prompt"""
        prompt = f"""You are an expert qualitative researcher analyzing citizen consultation interviews from Uruguay.

ANNOTATION GUIDELINES:
{guidelines}

Please analyze this interview and create a comprehensive annotation following the guidelines above:

INTERVIEW DATA:
{json.dumps(interview_data, indent=2, ensure_ascii=False)}

Create a complete annotation with:
1. Comprehensive tags (demographics, themes, emotions, etc.)
2. Rich thematic analysis of 2-4 major themes
3. Notable quotes with context (include turn_ids)
4. Conversation structure mapping
5. Research value assessment

Output only the JSON annotation structure, no additional text."""
        
        return prompt
    
    def save_annotation(self, interview_id, annotation_data):
        """Save annotation to file"""
        output_file = self.output_dir / f"{interview_id}_annotation.json"
        
        # Add metadata
        annotation_data['_metadata'] = {
            'annotated_at': datetime.now().isoformat(),
            'annotator': self.provider.get_model_name(),
            'guidelines_version': '1.0'
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(annotation_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved annotation for {interview_id}")
    
    def process_single_interview(self, interview_path, dry_run=False):
        """Process a single interview"""
        interview_id = interview_path.stem
        
        # Check if already processed
        if self.check_if_processed(interview_id):
            logger.info(f"Skipping {interview_id} - already processed")
            self.skipped.append(interview_id)
            return None
        
        logger.info(f"Processing {interview_id}...")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would process {interview_id}")
            return None
        
        # Check if provider is available
        if not self.provider:
            logger.error(f"LLM provider not initialized - skipping {interview_id}")
            self.failed.append((interview_id, "LLM provider not available"))
            return None
        
        try:
            # Load interview data
            with open(interview_path, 'r', encoding='utf-8') as f:
                interview_data = json.load(f)
            
            # Load guidelines
            guidelines = self.load_guidelines()
            
            # Create prompt
            prompt = self.create_annotation_prompt(interview_data, guidelines)
            
            # Call LLM provider
            temperature = self.config['processing'].get('temperature', 0.7)
            response_content = self.provider.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=4096
            )
            
            # Parse JSON response (handle markdown code blocks)
            try:
                # First try direct parsing
                annotation = json.loads(response_content)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                try:
                    import re
                    # Look for ```json ... ``` blocks
                    json_match = re.search(r'```json\s*(.*?)\s*```', response_content, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1)
                        annotation = json.loads(json_content)
                        logger.info(f"Successfully extracted JSON from markdown for {interview_id}")
                    else:
                        # Look for any ``` blocks
                        code_match = re.search(r'```\s*(.*?)\s*```', response_content, re.DOTALL)
                        if code_match:
                            json_content = code_match.group(1)
                            annotation = json.loads(json_content)
                            logger.info(f"Successfully extracted JSON from code block for {interview_id}")
                        else:
                            raise json.JSONDecodeError("No JSON found", response_content, 0)
                except json.JSONDecodeError:
                    # If all parsing attempts fail, wrap it
                    logger.warning(f"Response for {interview_id} not valid JSON, wrapping content")
                    annotation = {
                        "interview_id": interview_id,
                        "raw_response": response_content,
                        "parsing_error": "Response was not valid JSON"
                    }
            
            # Ensure interview_id is set
            if "interview_id" not in annotation:
                annotation["interview_id"] = interview_id
            
            # Save annotation
            self.save_annotation(interview_id, annotation)
            self.processed.append(interview_id)
            
            # Rate limiting - be respectful to API
            time.sleep(3)
            
            logger.info(f"Successfully processed {interview_id}")
            return annotation
            
        except Exception as e:
            logger.error(f"Failed to process {interview_id}: {e}")
            self.failed.append((interview_id, str(e)))
            return None
    
    def process_batch(self, interview_ids=None, dry_run=False):
        """Process multiple interviews"""
        interview_files = self.get_interview_files()
        
        if interview_ids:
            # Filter to specific IDs
            interview_files = [f for f in interview_files if f.stem in interview_ids]
        
        logger.info(f"Found {len(interview_files)} interviews to process")
        
        for i, interview_path in enumerate(interview_files):
            logger.info(f"Progress: {i+1}/{len(interview_files)}")
            self.process_single_interview(interview_path, dry_run)
        
        # Summary
        logger.info("\n=== BATCH PROCESSING SUMMARY ===")
        logger.info(f"Processed: {len(self.processed)}")
        logger.info(f"Skipped (already done): {len(self.skipped)}")
        logger.info(f"Failed: {len(self.failed)}")
        
        if self.failed:
            logger.error("\nFailed interviews:")
            for interview_id, error in self.failed:
                logger.error(f"  {interview_id}: {error}")
    
    def generate_corpus_summary(self):
        """Generate summary of all annotations"""
        annotations = []
        
        for ann_file in self.output_dir.glob("*_annotation.json"):
            if ann_file.stem.startswith("_"):  # Skip summary files
                continue
                
            with open(ann_file, 'r', encoding='utf-8') as f:
                annotations.append(json.load(f))
        
        # Create corpus summary
        summary = {
            'total_interviews': len(annotations),
            'annotation_date': datetime.now().isoformat(),
            'themes_distribution': self._analyze_themes(annotations),
            'location_distribution': self._analyze_locations(annotations),
            'interview_list': [a['interview_id'] for a in annotations]
        }
        
        summary_file = self.output_dir / "_corpus_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated corpus summary: {summary_file}")
    
    def _analyze_themes(self, annotations):
        """Analyze theme distribution across corpus"""
        theme_counts = {}
        
        for ann in annotations:
            if 'tags' in ann and 'themes' in ann['tags']:
                for theme in ann['tags']['themes']:
                    theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        return dict(sorted(theme_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_locations(self, annotations):
        """Analyze location distribution"""
        location_counts = {}
        
        for ann in annotations:
            if 'tags' in ann and 'location' in ann['tags']:
                for loc in ann['tags']['location']:
                    if loc not in ['urban_context', 'rural_context', 'small_town']:  # Skip generic
                        location_counts[loc] = location_counts.get(loc, 0) + 1
        
        return dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True))


def main():
    parser = argparse.ArgumentParser(
        description='Batch annotate Uruguay interviews using Kimi/Moonshot API',
        epilog='''
Examples:
  # Test run
  python batch_annotate_interviews.py --dry-run
  
  # Process specific interviews
  python batch_annotate_interviews.py --interviews 071 072 073
  
  # Process all interviews
  python batch_annotate_interviews.py
  
  # Only generate corpus summary
  python batch_annotate_interviews.py --summary-only

Note: Requires MOONSHOT_API_KEY environment variable to be set.
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--interviews', nargs='+', help='Specific interview IDs to process')
    parser.add_argument('--dry-run', action='store_true', help='Test run without API calls')
    parser.add_argument('--output-dir', help='Custom output directory')
    parser.add_argument('--summary-only', action='store_true', help='Only generate corpus summary')
    parser.add_argument('--provider', choices=['kimi', 'openai', 'gemini'], 
                       help='LLM provider to use (overrides config)')
    parser.add_argument('--model', help='Specific model to use (overrides config)')
    
    args = parser.parse_args()
    
    # Check API key early if not doing dry run or summary only
    if not args.dry_run and not args.summary_only:
        if not os.getenv("MOONSHOT_API_KEY"):
            logger.error("MOONSHOT_API_KEY not found in environment variables.")
            logger.error("Please set your Moonshot API key:")
            logger.error("  export MOONSHOT_API_KEY=your_api_key_here")
            logger.error("Or use --dry-run to test without API calls.")
            return 1
    
    # Initialize annotator
    annotator = InterviewAnnotator(
        output_dir=args.output_dir,
        provider_type=args.provider,
        model=args.model
    )
    
    if args.summary_only:
        annotator.generate_corpus_summary()
    else:
        # Process interviews
        annotator.process_batch(
            interview_ids=args.interviews,
            dry_run=args.dry_run
        )
        
        # Generate summary if not dry run
        if not args.dry_run:
            annotator.generate_corpus_summary()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)