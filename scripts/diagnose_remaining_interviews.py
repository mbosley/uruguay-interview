#!/usr/bin/env python3
"""
Diagnose which interviews didn't complete and why.
"""
import json
import sys
from pathlib import Path
from typing import Set, List, Dict, Any

def get_completed_interview_ids() -> Set[str]:
    """Get list of completed interview IDs."""
    production_dir = Path("data/processed/annotations/production")
    completed_ids = set()
    
    for file_path in production_dir.glob("*_final_annotation.json"):
        # Extract interview ID from filename
        interview_id = file_path.stem.replace("_final_annotation", "")
        completed_ids.add(interview_id)
    
    return completed_ids

def get_all_interview_ids() -> Dict[str, Dict]:
    """Get all interview files with metadata."""
    txt_dir = Path("data/processed/interviews_txt")
    interviews = {}
    
    for txt_file in txt_dir.glob("*.txt"):
        # Extract interview ID from filename 
        # Format: YYYYMMDD_HHMM_XXX.txt -> XXX
        parts = txt_file.stem.split("_")
        if len(parts) >= 3:
            interview_id = parts[2]
        else:
            interview_id = txt_file.stem
        
        # Get file info
        stat = txt_file.stat()
        word_count = 0
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                word_count = len(content.split())
        except Exception as e:
            print(f"⚠️  Could not read {txt_file}: {e}")
        
        interviews[interview_id] = {
            'file_path': txt_file,
            'file_size': stat.st_size,
            'word_count': word_count,
            'filename': txt_file.name
        }
    
    return interviews

def estimate_processing_difficulty(word_count: int) -> str:
    """Estimate processing difficulty based on word count."""
    if word_count < 3000:
        return "Easy"
    elif word_count < 6000:
        return "Medium" 
    elif word_count < 10000:
        return "Hard"
    else:
        return "Very Hard"

def analyze_missing_interviews():
    """Analyze which interviews are missing and their characteristics."""
    print("🔍 DIAGNOSING REMAINING INTERVIEWS")
    print("="*50)
    
    completed_ids = get_completed_interview_ids()
    all_interviews = get_all_interview_ids()
    
    print(f"📊 Overview:")
    print(f"   Total interviews: {len(all_interviews)}")
    print(f"   Completed: {len(completed_ids)}")
    print(f"   Remaining: {len(all_interviews) - len(completed_ids)}")
    print()
    
    # Find missing interviews
    missing_interviews = []
    for interview_id, info in all_interviews.items():
        if interview_id not in completed_ids:
            missing_interviews.append((interview_id, info))
    
    if not missing_interviews:
        print("✅ All interviews completed!")
        return
    
    print(f"❌ Missing {len(missing_interviews)} interviews:")
    print()
    
    # Sort by difficulty (word count)
    missing_interviews.sort(key=lambda x: x[1]['word_count'], reverse=True)
    
    total_words = 0
    difficulty_counts = {"Easy": 0, "Medium": 0, "Hard": 0, "Very Hard": 0}
    
    for interview_id, info in missing_interviews:
        difficulty = estimate_processing_difficulty(info['word_count'])
        difficulty_counts[difficulty] += 1
        total_words += info['word_count']
        
        print(f"   {interview_id}: {info['word_count']:,} words ({difficulty}) - {info['filename']}")
    
    print(f"\n📈 Missing Interview Analysis:")
    print(f"   Total words: {total_words:,}")
    print(f"   Average words: {total_words // len(missing_interviews):,}")
    print(f"   Difficulty breakdown:")
    for difficulty, count in difficulty_counts.items():
        if count > 0:
            print(f"     {difficulty}: {count} interviews")
    
    # Estimate processing time and cost
    # Based on our test: ~58s per interview average, but varies by size
    estimated_time_seconds = 0
    estimated_cost = 0.0
    
    for interview_id, info in missing_interviews:
        # Rough estimate: 60s base + 5s per 1000 words over 3000
        base_time = 60
        extra_words = max(0, info['word_count'] - 3000)
        extra_time = (extra_words / 1000) * 5
        interview_time = base_time + extra_time
        
        estimated_time_seconds += interview_time
        estimated_cost += 0.010  # Average cost per interview
    
    print(f"\n⏱️  Estimated Processing Time:")
    print(f"   Sequential: {estimated_time_seconds / 60:.1f} minutes")
    print(f"   Parallel (6 workers): {estimated_time_seconds / 6 / 60:.1f} minutes")
    print(f"   Estimated cost: ${estimated_cost:.2f}")
    
    # Check for very large interviews that might be causing timeouts
    large_interviews = [(id, info) for id, info in missing_interviews if info['word_count'] > 8000]
    if large_interviews:
        print(f"\n⚠️  Large Interviews (potential timeout issues):")
        for interview_id, info in large_interviews:
            estimated_turns = info['word_count'] // 100  # Rough estimate
            estimated_api_calls = 1 + (estimated_turns // 6)  # 1 + turn batches
            print(f"   {interview_id}: {info['word_count']:,} words, ~{estimated_turns} turns, ~{estimated_api_calls} API calls")
    
    # Check if there are any obvious patterns
    print(f"\n🔍 Pattern Analysis:")
    
    # Check by file size
    large_files = [info for _, info in missing_interviews if info['file_size'] > 30000]
    if large_files:
        print(f"   {len(large_files)} large files (>30KB) may need special handling")
    
    # Check by date
    dates = set()
    for _, info in missing_interviews:
        filename = info['filename']
        if len(filename) >= 8:
            date_part = filename[:8]
            dates.add(date_part)
    
    print(f"   Missing interviews span {len(dates)} dates")
    
    return missing_interviews

def main():
    """Main diagnostic function."""
    missing = analyze_missing_interviews()
    
    if missing:
        print(f"\n💡 Recommendations:")
        print(f"   1. Resume processing with same parallel script")
        print(f"   2. Consider processing large interviews separately")
        print(f"   3. Increase timeout for very large interviews")
        print(f"   4. Monitor for API rate limiting issues")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)