#!/usr/bin/env python3
"""
Pipeline status checker - provides comprehensive overview of current state.
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

def get_pipeline_status() -> Dict[str, Any]:
    """Get comprehensive pipeline status."""
    
    # Directory paths
    txt_dir = Path("data/processed/interviews_txt")
    production_dir = Path("data/processed/annotations/production")
    reports_dir = Path("data/reports")
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "directories": {},
        "interviews": {},
        "costs": {},
        "quality": {},
        "next_steps": []
    }
    
    # Check directory existence
    status["directories"] = {
        "raw_interviews": Path("data/raw/interviews").exists(),
        "processed_txt": txt_dir.exists(),
        "production_annotations": production_dir.exists(),
        "reports": reports_dir.exists()
    }
    
    # Interview analysis
    if txt_dir.exists():
        total_interviews = len(list(txt_dir.glob("*.txt")))
        status["interviews"]["total"] = total_interviews
    else:
        status["interviews"]["total"] = 0
        status["next_steps"].append("Process raw interviews to text format")
        return status
    
    # Annotation analysis
    if production_dir.exists():
        annotation_files = list(production_dir.glob("*_final_annotation.json"))
        completed_count = len(annotation_files)
        status["interviews"]["completed"] = completed_count
        status["interviews"]["remaining"] = status["interviews"]["total"] - completed_count
        status["interviews"]["completion_rate"] = (completed_count / status["interviews"]["total"]) * 100
        
        # Cost analysis
        total_cost = 0.0
        total_time = 0.0
        coverage_scores = []
        confidence_scores = []
        
        for file_path in annotation_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get('processing_metadata', {})
                annotation_data = data.get('annotation_data', {})
                
                total_cost += metadata.get('total_cost', 0)
                total_time += data.get('production_info', {}).get('processing_time', 0)
                
                coverage = metadata.get('turn_coverage', {}).get('coverage_percentage', 0)
                confidence = annotation_data.get('annotation_metadata', {}).get('overall_confidence', 0)
                
                coverage_scores.append(coverage)
                confidence_scores.append(confidence)
                
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
        
        status["costs"] = {
            "total_spent": total_cost,
            "avg_per_interview": total_cost / max(completed_count, 1),
            "estimated_remaining": (status["interviews"]["remaining"] * total_cost / max(completed_count, 1)) if completed_count > 0 else 0,
            "budget_utilization": (total_cost / 1.00) * 100
        }
        
        if coverage_scores:
            status["quality"] = {
                "avg_coverage": sum(coverage_scores) / len(coverage_scores),
                "min_coverage": min(coverage_scores),
                "max_coverage": max(coverage_scores),
                "perfect_coverage_count": sum(1 for s in coverage_scores if s >= 99.9),
                "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "total_processing_time": total_time / 60  # minutes
            }
    else:
        status["interviews"]["completed"] = 0
        status["interviews"]["remaining"] = status["interviews"]["total"]
        status["interviews"]["completion_rate"] = 0
        status["next_steps"].append("Run annotation pipeline")
    
    # Determine next steps
    if status["interviews"]["remaining"] > 0:
        status["next_steps"].append(f"Annotate {status['interviews']['remaining']} remaining interviews")
    
    if status["interviews"]["completed"] > 0 and not reports_dir.exists():
        status["next_steps"].append("Generate validation reports")
    
    if not status["next_steps"]:
        status["next_steps"].append("Pipeline complete - ready for analysis")
    
    return status

def print_status_report(status: Dict[str, Any]):
    """Print formatted status report."""
    
    print("📊 URUGUAY INTERVIEW PIPELINE STATUS")
    print("=" * 50)
    print(f"Timestamp: {status['timestamp']}")
    print()
    
    # Directory status
    print("📁 Directories:")
    dirs = status['directories']
    for name, exists in dirs.items():
        symbol = "✅" if exists else "❌"
        print(f"   {symbol} {name.replace('_', ' ').title()}")
    print()
    
    # Interview progress
    interviews = status['interviews']
    if 'total' in interviews and interviews['total'] > 0:
        print("📄 Interview Progress:")
        print(f"   Total interviews: {interviews['total']}")
        print(f"   Completed: {interviews.get('completed', 0)}")
        print(f"   Remaining: {interviews.get('remaining', 0)}")
        print(f"   Completion rate: {interviews.get('completion_rate', 0):.1f}%")
        print()
        
        # Progress bar
        completed = interviews.get('completed', 0)
        total = interviews['total']
        bar_length = 30
        filled = int(bar_length * completed / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"   Progress: [{bar}] {completed}/{total}")
        print()
    
    # Cost analysis
    if 'costs' in status and status['costs']:
        costs = status['costs']
        print("💰 Cost Analysis:")
        print(f"   Total spent: ${costs['total_spent']:.4f}")
        print(f"   Average per interview: ${costs['avg_per_interview']:.4f}")
        print(f"   Estimated remaining: ${costs['estimated_remaining']:.4f}")
        print(f"   Budget utilization: {costs['budget_utilization']:.1f}%")
        print()
    
    # Quality metrics
    if 'quality' in status and status['quality']:
        quality = status['quality']
        print("🎯 Quality Metrics:")
        print(f"   Average coverage: {quality['avg_coverage']:.1f}%")
        print(f"   Coverage range: {quality['min_coverage']:.1f}% - {quality['max_coverage']:.1f}%")
        print(f"   Perfect coverage: {quality['perfect_coverage_count']} interviews")
        print(f"   Average confidence: {quality['avg_confidence']:.2f}")
        print(f"   Total processing time: {quality['total_processing_time']:.1f} minutes")
        print()
    
    # Next steps
    if status['next_steps']:
        print("🚀 Next Steps:")
        for i, step in enumerate(status['next_steps'], 1):
            print(f"   {i}. {step}")
        print()
    
    # System readiness
    remaining = interviews.get('remaining', 0)
    if remaining > 0:
        estimated_time = remaining * 1.5  # 1.5 minutes per interview estimate
        estimated_cost = status.get('costs', {}).get('estimated_remaining', remaining * 0.01)
        print("⚡ Ready to Resume:")
        print(f"   Command: make annotate")
        print(f"   Estimated time: {estimated_time:.1f} minutes")
        print(f"   Estimated cost: ${estimated_cost:.2f}")
    else:
        print("✅ Annotation Complete:")
        print(f"   Command: make validate")
        print(f"   Ready for data extraction and analysis")

def main():
    """Main status function."""
    try:
        status = get_pipeline_status()
        print_status_report(status)
        return True
    except Exception as e:
        print(f"❌ Error getting pipeline status: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)