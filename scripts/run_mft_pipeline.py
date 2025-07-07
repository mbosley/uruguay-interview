#!/usr/bin/env python3
"""
Run MFT-enhanced annotation pipeline on all interviews.
Processes all 36 interviews with 6-dimensional analysis.
"""

import asyncio
import sqlite3
from pathlib import Path
import sys
import time
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline.ingestion.document_processor import DocumentProcessor
from src.pipeline.annotation.multipass_annotator import MultiPassAnnotator
from src.pipeline.annotation.moral_foundations_analyzer import MoralFoundationsAnalyzer
from src.database.connection import get_db_connection


async def process_single_interview(file_path: Path, annotator: MultiPassAnnotator) -> dict:
    """Process a single interview with MFT annotation."""
    interview_id = file_path.stem
    
    print(f"\n📄 Processing {interview_id}...")
    
    try:
        # Load interview
        processor = DocumentProcessor()
        interview = processor.process_interview(file_path)
        
        # Run annotation
        start_time = time.time()
        annotation_data, metadata = await annotator.annotate_interview(interview)
        processing_time = time.time() - start_time
        
        # Extract MFT summary
        turns = annotation_data['conversation_analysis']['turns']
        mft_count = sum(1 for t in turns 
                       if t.get('moral_foundations_analysis', {}).get('dominant_foundation', 'none') != 'none')
        
        print(f"   ✓ Completed in {processing_time:.1f}s")
        print(f"   ✓ {len(turns)} turns analyzed")
        print(f"   ✓ {mft_count} turns with moral content")
        print(f"   ✓ Cost: ${metadata['total_cost']:.4f}")
        
        return {
            'success': True,
            'interview_id': interview_id,
            'annotation_data': annotation_data,
            'metadata': metadata,
            'mft_turns': mft_count
        }
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        return {
            'success': False,
            'interview_id': interview_id,
            'error': str(e)
        }


def store_mft_data(conn: sqlite3.Connection, interview_id: str, annotation_data: dict):
    """Store MFT data in database."""
    cursor = conn.cursor()
    
    # Get turns with MFT data
    turns = annotation_data['conversation_analysis']['turns']
    
    # Store turn-level MFT data
    for turn in turns:
        if 'moral_foundations_analysis' not in turn:
            continue
            
        mft = turn['moral_foundations_analysis']
        
        # Get turn ID from database
        cursor.execute("""
            SELECT id FROM turns 
            WHERE interview_id = ? AND turn_number = ?
        """, (interview_id, turn['turn_id']))
        
        result = cursor.fetchone()
        if not result:
            continue
            
        turn_db_id = result[0]
        
        # Insert MFT data
        cursor.execute("""
            INSERT INTO turn_moral_foundations (
                turn_id, reasoning, care_harm, fairness_cheating,
                loyalty_betrayal, authority_subversion, sanctity_degradation,
                liberty_oppression, dominant_foundation, foundations_narrative,
                mft_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            turn_db_id,
            mft.get('reasoning', ''),
            mft.get('care_harm', 0.0),
            mft.get('fairness_cheating', 0.0),
            mft.get('loyalty_betrayal', 0.0),
            mft.get('authority_subversion', 0.0),
            mft.get('sanctity_degradation', 0.0),
            mft.get('liberty_oppression', 0.0),
            mft.get('dominant_foundation', 'none'),
            mft.get('foundations_narrative', ''),
            mft.get('mft_confidence', 0.0)
        ))
    
    # Calculate and store interview-level aggregates
    analyzer = MoralFoundationsAnalyzer()
    mft_analyses = [t['moral_foundations_analysis'] for t in turns 
                   if 'moral_foundations_analysis' in t]
    
    if mft_analyses:
        profile = analyzer.analyze_interview_aggregate(mft_analyses)
        
        # Store aggregate
        cursor.execute("""
            INSERT INTO interview_moral_foundations (
                interview_id, avg_care_harm, avg_fairness_cheating,
                avg_loyalty_betrayal, avg_authority_subversion,
                avg_sanctity_degradation, avg_liberty_oppression,
                primary_foundation_1, primary_foundation_2, primary_foundation_3,
                moral_profile_narrative, total_moral_engagement
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interview_id,
            profile['average_scores']['care_harm'],
            profile['average_scores']['fairness_cheating'],
            profile['average_scores']['loyalty_betrayal'],
            profile['average_scores']['authority_subversion'],
            profile['average_scores']['sanctity_degradation'],
            profile['average_scores']['liberty_oppression'],
            profile['primary_foundations'][0] if len(profile['primary_foundations']) > 0 else None,
            profile['primary_foundations'][1] if len(profile['primary_foundations']) > 1 else None,
            profile['primary_foundations'][2] if len(profile['primary_foundations']) > 2 else None,
            profile['moral_profile_narrative'],
            profile['total_moral_engagement']
        ))
    
    conn.commit()


async def main():
    """Run MFT annotation on all interviews."""
    print("🚀 Uruguay Interview MFT Annotation Pipeline")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get all interview files
    txt_dir = project_root / "data" / "processed" / "interviews_txt"
    interview_files = sorted(txt_dir.glob("*.txt"))
    
    print(f"\n📊 Found {len(interview_files)} interviews to process")
    
    # Check if MFT tables exist
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='turn_moral_foundations'
    """)
    if not cursor.fetchone():
        print("\n❌ MFT tables not found! Run 'python scripts/add_mft_tables.py' first")
        return
    
    # Initialize annotator
    annotator = MultiPassAnnotator(
        model_name="gpt-4o-mini",
        temperature=0.1,
        turns_per_batch=6
    )
    
    # Process interviews
    print("\n🔄 Processing interviews...")
    results = []
    total_cost = 0.0
    
    for i, file_path in enumerate(interview_files, 1):
        print(f"\n[{i}/{len(interview_files)}]", end="")
        result = await process_single_interview(file_path, annotator)
        results.append(result)
        
        if result['success']:
            total_cost += result['metadata']['total_cost']
            
            # Store in database
            try:
                store_mft_data(conn, result['interview_id'], result['annotation_data'])
                print(f"   ✓ Stored MFT data in database")
            except Exception as e:
                print(f"   ⚠️  Failed to store in database: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/{len(interview_files)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"💰 Total cost: ${total_cost:.2f}")
    print(f"📊 Total MFT turns: {sum(r.get('mft_turns', 0) for r in successful)}")
    
    if failed:
        print("\n❌ Failed interviews:")
        for r in failed:
            print(f"   - {r['interview_id']}: {r['error']}")
    
    # Save summary
    summary_file = project_root / f"mft_annotation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_interviews': len(interview_files),
            'successful': len(successful),
            'failed': len(failed),
            'total_cost': total_cost,
            'results': results
        }, f, indent=2)
    
    print(f"\n📄 Summary saved to: {summary_file}")
    print(f"\n✅ MFT annotation pipeline completed!")
    
    conn.close()


if __name__ == "__main__":
    asyncio.run(main())