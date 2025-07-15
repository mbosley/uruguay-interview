"""
Batch process all interview text files into structured JSON
"""

import json
import sys
from pathlib import Path

# Add src to path so we can import our parser
sys.path.append(str(Path(__file__).parent.parent / "src"))

from parser.interview_parser import InterviewParser

def process_all_interviews():
    """Convert all interview text files to structured JSON"""
    
    # Set up paths
    input_dir = Path("../data/processed/interviews_txt")
    output_dir = Path("../data/processed/structured")
    output_dir.mkdir(exist_ok=True)
    
    parser = InterviewParser()
    
    # Find all interview text files
    txt_files = list(input_dir.glob("*.txt"))
    
    print(f"🔍 Found {len(txt_files)} interview files")
    
    results = []
    errors = []
    
    for txt_file in sorted(txt_files):
        try:
            # Parse the interview
            interview_data = parser.parse_file(txt_file)
            
            # Save individual JSON file
            output_file = output_dir / f"{interview_data['interview_id']}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(interview_data, f, indent=2, ensure_ascii=False)
            
            results.append({
                'file': txt_file.name,
                'interview_id': interview_data['interview_id'],
                'turns': interview_data['total_turns'],
                'location': interview_data['metadata'].get('location', 'Unknown')
            })
            
            print(f"✅ {interview_data['interview_id']}: {interview_data['total_turns']} turns")
            
        except Exception as e:
            errors.append({'file': txt_file.name, 'error': str(e)})
            print(f"❌ {txt_file.name}: {e}")
    
    # Create summary file
    summary = {
        'total_interviews': len(results),
        'total_turns': sum(r['turns'] for r in results),
        'successful_parses': results,
        'errors': errors,
        'processed_at': interview_data['parsed_at'] if results else None
    }
    
    summary_file = output_dir / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Successfully parsed: {len(results)} interviews")
    print(f"   Total turns extracted: {summary['total_turns']}")
    print(f"   Errors: {len(errors)}")
    print(f"   Output directory: {output_dir}")
    
    if errors:
        print(f"\n❌ Errors:")
        for error in errors:
            print(f"   {error['file']}: {error['error']}")
    
    return summary

def create_consolidated_corpus():
    """Create a single file with all interviews for easy searching"""
    
    structured_dir = Path("../data/processed/structured")
    
    if not structured_dir.exists():
        print("❌ No structured data found. Run process_all_interviews() first.")
        return
    
    # Load all individual interview JSONs
    all_interviews = []
    
    for json_file in sorted(structured_dir.glob("*.json")):
        if json_file.name.startswith("_"):  # Skip summary files
            continue
            
        with open(json_file, 'r', encoding='utf-8') as f:
            interview = json.load(f)
            all_interviews.append(interview)
    
    # Create consolidated corpus
    corpus = {
        'corpus_info': {
            'total_interviews': len(all_interviews),
            'interview_ids': [i['interview_id'] for i in all_interviews],
            'total_turns': sum(i['total_turns'] for i in all_interviews),
            'date_range': 'May 28-29, 2025',
            'location': 'Uruguay'
        },
        'interviews': all_interviews
    }
    
    # Save consolidated file
    corpus_file = structured_dir / "_corpus.json"
    
    with open(corpus_file, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)
    
    print(f"📚 Created consolidated corpus: {corpus_file}")
    print(f"   {corpus['corpus_info']['total_interviews']} interviews")
    print(f"   {corpus['corpus_info']['total_turns']} total turns")
    
    return corpus

if __name__ == "__main__":
    print("🚀 Processing all Uruguay interviews...")
    summary = process_all_interviews()
    
    if summary['total_interviews'] > 0:
        print("\n📚 Creating consolidated corpus...")
        create_consolidated_corpus()
    
    print("\n✨ Done! Ready for search CLI implementation.")