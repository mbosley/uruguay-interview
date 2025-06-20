#!/usr/bin/env python3
"""
Robust validation pipeline for annotation quality assessment.
"""
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def validate_annotation_quality(annotation_file: Path) -> Dict[str, Any]:
    """Validate quality of a single annotation."""
    try:
        with open(annotation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        annotation_data = data.get('annotation_data', {})
        metadata = data.get('processing_metadata', {})
        
        # Extract key metrics
        interview_id = annotation_data.get('interview_metadata', {}).get('interview_id', 'unknown')
        
        # Turn coverage analysis
        turn_coverage = metadata.get('turn_coverage', {})
        coverage_pct = turn_coverage.get('coverage_percentage', 0)
        analyzed_turns = turn_coverage.get('analyzed_turns', 0)
        total_turns = turn_coverage.get('total_turns', 0)
        
        # Quality metrics
        overall_confidence = annotation_data.get('annotation_metadata', {}).get('overall_confidence', 0)
        
        # Data completeness
        national_priorities = annotation_data.get('priority_analysis', {}).get('national_priorities', [])
        local_priorities = annotation_data.get('priority_analysis', {}).get('local_priorities', [])
        conversation_turns = annotation_data.get('conversation_analysis', {}).get('turns', [])
        
        # Cost metrics
        cost = metadata.get('total_cost', 0)
        api_calls = metadata.get('total_api_calls', 0)
        processing_time = data.get('production_info', {}).get('processing_time', 0)
        
        # Quality assessment
        quality_issues = []
        
        if coverage_pct < 95:
            quality_issues.append(f"Low turn coverage: {coverage_pct:.1f}%")
        
        if overall_confidence < 0.7:
            quality_issues.append(f"Low confidence: {overall_confidence:.2f}")
        
        if len(national_priorities) < 3:
            quality_issues.append(f"Insufficient national priorities: {len(national_priorities)}")
        
        if len(local_priorities) < 3:
            quality_issues.append(f"Insufficient local priorities: {len(local_priorities)}")
        
        if len(conversation_turns) != analyzed_turns:
            quality_issues.append(f"Turn count mismatch: {len(conversation_turns)} vs {analyzed_turns}")
        
        # Calculate quality score
        quality_score = 1.0
        if quality_issues:
            quality_score = max(0.0, 1.0 - (len(quality_issues) * 0.15))
        
        return {
            'interview_id': interview_id,
            'file_path': str(annotation_file),
            'quality_score': quality_score,
            'quality_issues': quality_issues,
            'metrics': {
                'coverage_percentage': coverage_pct,
                'analyzed_turns': analyzed_turns,
                'total_turns': total_turns,
                'overall_confidence': overall_confidence,
                'national_priorities_count': len(national_priorities),
                'local_priorities_count': len(local_priorities),
                'conversation_turns_count': len(conversation_turns),
                'cost': cost,
                'api_calls': api_calls,
                'processing_time': processing_time
            },
            'validation_timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'interview_id': 'error',
            'file_path': str(annotation_file),
            'quality_score': 0.0,
            'quality_issues': [f"Validation error: {str(e)}"],
            'metrics': {},
            'validation_timestamp': datetime.now().isoformat()
        }

def generate_validation_report(input_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """Generate comprehensive validation report."""
    
    print("🔍 Validating annotation quality...")
    
    # Find all annotation files
    annotation_files = list(input_dir.glob("*_final_annotation.json"))
    
    if not annotation_files:
        return {
            "error": "No annotation files found",
            "input_dir": str(input_dir)
        }
    
    print(f"📄 Found {len(annotation_files)} annotation files")
    
    # Validate each file
    validation_results = []
    for file_path in annotation_files:
        result = validate_annotation_quality(file_path)
        validation_results.append(result)
        
        # Print progress
        quality_score = result['quality_score']
        issues_count = len(result['quality_issues'])
        symbol = "✅" if quality_score >= 0.9 else "⚠️" if quality_score >= 0.7 else "❌"
        
        print(f"   {symbol} {result['interview_id']}: {quality_score:.2f} quality ({issues_count} issues)")
    
    # Calculate aggregate metrics
    successful_validations = [r for r in validation_results if r['quality_score'] > 0]
    
    if not successful_validations:
        return {
            "error": "No successful validations",
            "validation_results": validation_results
        }
    
    # Aggregate statistics
    total_files = len(validation_results)
    high_quality_count = sum(1 for r in successful_validations if r['quality_score'] >= 0.9)
    medium_quality_count = sum(1 for r in successful_validations if 0.7 <= r['quality_score'] < 0.9)
    low_quality_count = sum(1 for r in successful_validations if r['quality_score'] < 0.7)
    
    # Cost and performance metrics
    total_cost = sum(r['metrics'].get('cost', 0) for r in successful_validations)
    total_time = sum(r['metrics'].get('processing_time', 0) for r in successful_validations)
    total_turns = sum(r['metrics'].get('analyzed_turns', 0) for r in successful_validations)
    total_expected_turns = sum(r['metrics'].get('total_turns', 0) for r in successful_validations)
    
    # Coverage metrics
    coverage_scores = [r['metrics'].get('coverage_percentage', 0) for r in successful_validations]
    confidence_scores = [r['metrics'].get('overall_confidence', 0) for r in successful_validations]
    
    # Generate comprehensive report
    report = {
        "validation_summary": {
            "total_annotations": total_files,
            "successful_validations": len(successful_validations),
            "validation_success_rate": (len(successful_validations) / total_files) * 100,
            "quality_distribution": {
                "high_quality": high_quality_count,
                "medium_quality": medium_quality_count,
                "low_quality": low_quality_count
            },
            "quality_percentages": {
                "high_quality_rate": (high_quality_count / len(successful_validations)) * 100,
                "medium_quality_rate": (medium_quality_count / len(successful_validations)) * 100,
                "low_quality_rate": (low_quality_count / len(successful_validations)) * 100
            }
        },
        "performance_metrics": {
            "total_cost": total_cost,
            "avg_cost_per_interview": total_cost / len(successful_validations),
            "total_processing_time_minutes": total_time / 60,
            "avg_processing_time_seconds": total_time / len(successful_validations),
            "total_turns_analyzed": total_turns,
            "total_expected_turns": total_expected_turns,
            "overall_coverage_rate": (total_turns / total_expected_turns) * 100 if total_expected_turns > 0 else 0
        },
        "quality_metrics": {
            "avg_quality_score": sum(r['quality_score'] for r in successful_validations) / len(successful_validations),
            "min_quality_score": min(r['quality_score'] for r in successful_validations),
            "max_quality_score": max(r['quality_score'] for r in successful_validations),
            "avg_coverage_percentage": sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0,
            "min_coverage_percentage": min(coverage_scores) if coverage_scores else 0,
            "max_coverage_percentage": max(coverage_scores) if coverage_scores else 0,
            "perfect_coverage_count": sum(1 for score in coverage_scores if score >= 99.9),
            "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        },
        "detailed_results": validation_results,
        "validation_timestamp": datetime.now().isoformat(),
        "input_directory": str(input_dir),
        "output_directory": str(output_dir)
    }
    
    return report

def print_validation_summary(report: Dict[str, Any]):
    """Print formatted validation summary."""
    
    if "error" in report:
        print(f"❌ Validation failed: {report['error']}")
        return
    
    summary = report['validation_summary']
    performance = report['performance_metrics']
    quality = report['quality_metrics']
    
    print("\n" + "="*60)
    print("🎯 ANNOTATION VALIDATION REPORT")
    print("="*60)
    
    print(f"\n📊 Validation Summary:")
    print(f"   Total annotations: {summary['total_annotations']}")
    print(f"   Successful validations: {summary['successful_validations']}")
    print(f"   Validation success rate: {summary['validation_success_rate']:.1f}%")
    
    print(f"\n🏆 Quality Distribution:")
    quality_dist = summary['quality_distribution']
    quality_pct = summary['quality_percentages']
    print(f"   High quality (≥90%): {quality_dist['high_quality']} ({quality_pct['high_quality_rate']:.1f}%)")
    print(f"   Medium quality (70-89%): {quality_dist['medium_quality']} ({quality_pct['medium_quality_rate']:.1f}%)")
    print(f"   Low quality (<70%): {quality_dist['low_quality']} ({quality_pct['low_quality_rate']:.1f}%)")
    
    print(f"\n💰 Performance Metrics:")
    print(f"   Total cost: ${performance['total_cost']:.4f}")
    print(f"   Average cost per interview: ${performance['avg_cost_per_interview']:.4f}")
    print(f"   Total processing time: {performance['total_processing_time_minutes']:.1f} minutes")
    print(f"   Average processing time: {performance['avg_processing_time_seconds']:.1f} seconds")
    
    print(f"\n🎯 Quality Metrics:")
    print(f"   Average quality score: {quality['avg_quality_score']:.3f}")
    print(f"   Quality score range: {quality['min_quality_score']:.3f} - {quality['max_quality_score']:.3f}")
    print(f"   Average coverage: {quality['avg_coverage_percentage']:.1f}%")
    print(f"   Coverage range: {quality['min_coverage_percentage']:.1f}% - {quality['max_coverage_percentage']:.1f}%")
    print(f"   Perfect coverage interviews: {quality['perfect_coverage_count']}")
    print(f"   Average confidence: {quality['avg_confidence']:.2f}")
    print(f"   Overall coverage rate: {performance['overall_coverage_rate']:.1f}%")
    
    print(f"\n📋 Turn Analysis:")
    print(f"   Total turns analyzed: {performance['total_turns_analyzed']:,}")
    print(f"   Total expected turns: {performance['total_expected_turns']:,}")
    print(f"   Coverage completeness: {performance['overall_coverage_rate']:.1f}%")

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Robust annotation validation")
    parser.add_argument("--input-dir", type=Path, required=True, help="Input directory with annotations")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for reports")
    parser.add_argument("--log-file", type=Path, help="Log file path")
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate validation report
        report = generate_validation_report(args.input_dir, args.output_dir)
        
        # Print summary
        print_validation_summary(report)
        
        # Save detailed report
        report_file = args.output_dir / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        # Return success based on quality metrics
        if "error" not in report:
            avg_quality = report['quality_metrics']['avg_quality_score']
            success_rate = report['validation_summary']['validation_success_rate']
            
            if avg_quality >= 0.8 and success_rate >= 95:
                print(f"\n✅ Validation successful - high quality annotations")
                return True
            else:
                print(f"\n⚠️  Validation completed with quality concerns")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)