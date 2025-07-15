#!/usr/bin/env python3
"""
Merge rich annotations with parsed interview data to create unified searchable structure
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnnotationMerger:
    """Merges rich annotations with parsed interview data"""
    
    def __init__(self, annotations_dir=None, output_dir=None):
        self.project_root = Path(__file__).parent.parent.parent
        self.structured_dir = self.project_root / "data" / "processed" / "structured"
        
        if annotations_dir:
            self.annotations_dir = Path(annotations_dir)
        else:
            self.annotations_dir = self.project_root / "data" / "processed" / "annotations" / "searchable"
        
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.project_root / "data" / "processed" / "enriched"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track progress
        self.merged = []
        self.failed = []
        self.skipped = []
    
    def get_available_interviews(self):
        """Get interviews that have both structured data and annotations"""
        structured_files = set(f.stem for f in self.structured_dir.glob("[0-9]*.json"))
        annotation_files = set(f.stem.replace("_annotation", "") for f in self.annotations_dir.glob("[0-9]*_annotation.json"))
        
        # Return intersection - interviews with both files
        available = structured_files & annotation_files
        return sorted(list(available))
    
    def load_interview_data(self, interview_id):
        """Load structured interview data"""
        interview_path = self.structured_dir / f"{interview_id}.json"
        if not interview_path.exists():
            raise FileNotFoundError(f"Interview data not found: {interview_path}")
        
        with open(interview_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_annotation_data(self, interview_id):
        """Load annotation data"""
        annotation_path = self.annotations_dir / f"{interview_id}_annotation.json"
        if not annotation_path.exists():
            raise FileNotFoundError(f"Annotation not found: {annotation_path}")
        
        with open(annotation_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def merge_single_interview(self, interview_id):
        """Merge structured data with annotation for single interview"""
        try:
            # Load both datasets
            interview_data = self.load_interview_data(interview_id)
            annotation_data = self.load_annotation_data(interview_id)
            
            # Create enriched structure
            enriched = {
                "interview_id": interview_id,
                "metadata": {
                    "original_file": interview_data.get("metadata", {}).get("original_file", ""),
                    "participants": interview_data.get("metadata", {}).get("participants", []),
                    "total_turns": interview_data.get("metadata", {}).get("total_turns", 0),
                    "parsed_at": interview_data.get("metadata", {}).get("parsed_at", ""),
                    "annotated_at": annotation_data.get("_metadata", {}).get("annotated_at", ""),
                    "merged_at": datetime.now().isoformat()
                },
                
                # Rich summary and tags from annotation
                "annotation": {
                    "tags": annotation_data.get("tags", {}),
                    "summary": annotation_data.get("summary", {}),
                    "notable_quotes": annotation_data.get("summary", {}).get("notable_quotes", []),
                    "key_themes": annotation_data.get("summary", {}).get("key_themes", []),
                    "conversation_structure": annotation_data.get("summary", {}).get("conversation_structure", {}),
                    "research_notes": annotation_data.get("summary", {}).get("research_notes", "")
                },
                
                # Full turn-by-turn data with searchable structure
                "turns": interview_data.get("turns", []),
                
                # Create searchable indexes
                "indexes": self._create_indexes(interview_data, annotation_data)
            }
            
            return enriched
            
        except Exception as e:
            logger.error(f"Failed to merge {interview_id}: {e}")
            raise
    
    def _create_indexes(self, interview_data, annotation_data):
        """Create searchable indexes for quick lookup"""
        indexes = {
            "turn_by_id": {},
            "turns_by_speaker": {},
            "turns_by_theme": {},
            "notable_quote_turns": set()
        }
        
        # Index turns by ID and speaker
        for turn in interview_data.get("turns", []):
            turn_id = turn["turn_id"]
            speaker = turn["speaker"]
            
            indexes["turn_by_id"][turn_id] = turn
            
            if speaker not in indexes["turns_by_speaker"]:
                indexes["turns_by_speaker"][speaker] = []
            indexes["turns_by_speaker"][speaker].append(turn_id)
        
        # Index turns mentioned in notable quotes
        for quote in annotation_data.get("summary", {}).get("notable_quotes", []):
            if "turn" in quote:
                indexes["notable_quote_turns"].add(quote["turn"])
        
        # Index turns by themes (from key_themes elaboration_turns)
        for theme in annotation_data.get("summary", {}).get("key_themes", []):
            theme_name = theme.get("theme", "unknown")
            if theme_name not in indexes["turns_by_theme"]:
                indexes["turns_by_theme"][theme_name] = []
            
            # Add primary evidence turns
            for evidence in theme.get("primary_evidence", []):
                if "turn" in evidence:
                    indexes["turns_by_theme"][theme_name].append(evidence["turn"])
            
            # Add elaboration turns
            for turn_id in theme.get("elaboration_turns", []):
                if turn_id not in indexes["turns_by_theme"][theme_name]:
                    indexes["turns_by_theme"][theme_name].append(turn_id)
        
        # Convert set to list for JSON serialization
        indexes["notable_quote_turns"] = list(indexes["notable_quote_turns"])
        
        return indexes
    
    def save_enriched_interview(self, interview_id, enriched_data):
        """Save enriched interview data"""
        output_file = self.output_dir / f"{interview_id}_enriched.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved enriched interview: {output_file}")
    
    def merge_interviews(self, interview_ids=None, force_reprocess=False):
        """Merge multiple interviews"""
        if interview_ids is None:
            interview_ids = self.get_available_interviews()
        else:
            # Filter to only those that have both files
            available = self.get_available_interviews()
            interview_ids = [iid for iid in interview_ids if iid in available]
        
        logger.info(f"Found {len(interview_ids)} interviews to merge: {interview_ids}")
        
        for i, interview_id in enumerate(interview_ids):
            logger.info(f"Progress: {i+1}/{len(interview_ids)} - {interview_id}")
            
            # Check if already processed
            output_file = self.output_dir / f"{interview_id}_enriched.json"
            if output_file.exists() and not force_reprocess:
                logger.info(f"Skipping {interview_id} - already enriched")
                self.skipped.append(interview_id)
                continue
            
            try:
                enriched_data = self.merge_single_interview(interview_id)
                self.save_enriched_interview(interview_id, enriched_data)
                self.merged.append(interview_id)
                
            except Exception as e:
                logger.error(f"Failed to merge {interview_id}: {e}")
                self.failed.append((interview_id, str(e)))
        
        # Summary
        logger.info("\n=== MERGE SUMMARY ===")
        logger.info(f"Merged: {len(self.merged)}")
        logger.info(f"Skipped (already done): {len(self.skipped)}")
        logger.info(f"Failed: {len(self.failed)}")
        
        if self.failed:
            logger.error("\nFailed interviews:")
            for interview_id, error in self.failed:
                logger.error(f"  {interview_id}: {error}")
    
    def create_enriched_corpus_summary(self):
        """Create summary of all enriched interviews"""
        enriched_files = list(self.output_dir.glob("*_enriched.json"))
        
        corpus_summary = {
            "total_enriched_interviews": len(enriched_files),
            "created_at": datetime.now().isoformat(),
            "interviews": []
        }
        
        for enriched_file in sorted(enriched_files):
            interview_id = enriched_file.stem.replace("_enriched", "")
            
            # Load basic metadata
            try:
                with open(enriched_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                corpus_summary["interviews"].append({
                    "interview_id": interview_id,
                    "total_turns": data["metadata"]["total_turns"],
                    "themes": list(data["indexes"]["turns_by_theme"].keys()),
                    "speakers": list(data["indexes"]["turns_by_speaker"].keys()),
                    "notable_quotes_count": len(data["annotation"]["notable_quotes"])
                })
                
            except Exception as e:
                logger.warning(f"Could not process {enriched_file}: {e}")
        
        # Save corpus summary
        summary_file = self.output_dir / "_enriched_corpus_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(corpus_summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created enriched corpus summary: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Merge rich annotations with parsed interview data',
        epilog='''
Examples:
  # Merge all available interviews
  python merge_annotations.py
  
  # Merge specific interviews
  python merge_annotations.py --interviews 071 072
  
  # Force reprocessing (overwrite existing)
  python merge_annotations.py --force
  
  # Custom output directory
  python merge_annotations.py --output-dir /path/to/output
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--interviews', nargs='+', help='Specific interview IDs to merge')
    parser.add_argument('--force', action='store_true', help='Force reprocessing of existing files')
    parser.add_argument('--annotations-dir', help='Directory containing annotation files')
    parser.add_argument('--output-dir', help='Custom output directory')
    
    args = parser.parse_args()
    
    # Initialize merger
    merger = AnnotationMerger(
        annotations_dir=args.annotations_dir,
        output_dir=args.output_dir
    )
    
    # Merge interviews
    merger.merge_interviews(
        interview_ids=args.interviews,
        force_reprocess=args.force
    )
    
    # Create corpus summary
    merger.create_enriched_corpus_summary()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)