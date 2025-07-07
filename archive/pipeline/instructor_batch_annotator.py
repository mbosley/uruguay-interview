"""
Batch processing system for Instructor-based annotations.
Handles all 37 interviews efficiently with cost tracking.
"""
import instructor
import json
from openai import OpenAI
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import logging
import time
from datetime import datetime
import xml.etree.ElementTree as ET

from src.pipeline.annotation.instructor_models import CompleteInterviewAnnotation
from src.pipeline.ingestion.document_processor import DocumentProcessor, InterviewDocument
from src.config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class InstructorBatchAnnotator:
    """Batch processing system for efficient interview annotation using Instructor."""
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",  # Start with cheaper model
        temperature: float = 0.1,
        max_retries: int = 3,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize batch annotator.
        
        Args:
            model_name: OpenAI model to use
            temperature: Sampling temperature
            max_retries: Maximum validation retries
            output_dir: Directory to save results
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.output_dir = Path(output_dir) if output_dir else Path("data/processed/instructor_annotations")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client with Instructor
        config_loader = ConfigLoader()
        api_key = config_loader.get_api_key("openai")
        if not api_key:
            raise ValueError("No OpenAI API key found")
        
        openai_client = OpenAI(api_key=api_key)
        self.client = instructor.from_openai(openai_client)
        
        # Cost tracking
        self.total_cost = 0.0
        self.successful_annotations = 0
        self.failed_annotations = 0
        
        logger.info(f"Initialized batch annotator with model {model_name}")
    
    def create_simplified_prompt(self, interview: InterviewDocument) -> str:
        """Create a focused prompt that's more likely to succeed."""
        return f"""
You are an expert qualitative researcher analyzing a citizen consultation interview from Uruguay.

INTERVIEW TO ANALYZE:
{interview.text}

INTERVIEW METADATA:
- ID: {interview.id}
- Date: {interview.date}
- Location: {interview.location}

Provide a complete systematic analysis following the structured schema.

CRITICAL REQUIREMENTS:
1. Analyze EVERY conversation turn with detailed reasoning
2. Extract exactly 3 national priorities and 3 local priorities (ranked 1, 2, 3)
3. Provide chain-of-thought reasoning for all annotation decisions
4. Be thorough but stay within the required structure
5. Use the participant's own words when possible

Focus on accuracy and completeness. Every field in the schema must be filled.
"""
    
    def annotate_single_interview(self, interview: InterviewDocument) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Annotate a single interview with error handling.
        
        Returns:
            Tuple of (success, result_data, error_message)
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting annotation for interview {interview.id}")
            
            # Create prompt
            prompt = self.create_simplified_prompt(interview)
            
            # Make API call with Instructor
            annotation = self.client.chat.completions.create(
                model=self.model_name,
                response_model=CompleteInterviewAnnotation,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert qualitative researcher. Follow the structured schema exactly. Every field must be completed."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_retries=self.max_retries
            )
            
            processing_time = time.time() - start_time
            
            # Create result data
            result_data = {
                "interview_id": annotation.interview_id,
                "annotation": annotation.model_dump(),
                "metadata": {
                    "model_name": self.model_name,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat(),
                    "total_turns": len(annotation.turns),
                    "confidence": annotation.overall_confidence
                }
            }
            
            # Estimate cost (rough)
            estimated_cost = self._estimate_cost(interview, len(annotation.turns))
            self.total_cost += estimated_cost
            result_data["metadata"]["estimated_cost"] = estimated_cost
            
            self.successful_annotations += 1
            logger.info(f"Successfully annotated interview {interview.id} with {len(annotation.turns)} turns in {processing_time:.1f}s")
            
            return True, result_data, None
            
        except Exception as e:
            self.failed_annotations += 1
            error_msg = f"Failed to annotate interview {interview.id}: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def _estimate_cost(self, interview: InterviewDocument, output_turns: int) -> float:
        """Estimate the cost of an annotation."""
        # Rough token estimates
        input_tokens = len(interview.text.split()) * 1.3 + 1000  # Interview + prompt
        output_tokens = output_turns * 30 + 500  # Rough estimate based on turns
        
        # GPT-4o-mini pricing
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        
        return input_cost + output_cost
    
    def process_all_interviews(self, max_interviews: Optional[int] = None) -> Dict[str, Any]:
        """
        Process all interviews in the dataset.
        
        Args:
            max_interviews: Limit number of interviews (for testing)
            
        Returns:
            Summary statistics
        """
        # Find all interview files
        txt_dir = Path("data/processed/interviews_txt")
        txt_files = list(txt_dir.glob("*.txt"))
        
        if not txt_files:
            raise ValueError("No interview files found")
        
        # Limit for testing
        if max_interviews:
            txt_files = txt_files[:max_interviews]
        
        logger.info(f"Processing {len(txt_files)} interviews")
        
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Process each interview
        results = []
        start_time = time.time()
        
        for i, txt_file in enumerate(txt_files, 1):
            try:
                # Process interview document
                interview = processor.process_interview(txt_file)
                
                # Annotate
                success, result_data, error_msg = self.annotate_single_interview(interview)
                
                if success:
                    # Save result
                    output_file = self.output_dir / f"{interview.id}_instructor_annotation.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result_data, f, indent=2, ensure_ascii=False)
                    
                    results.append({
                        "interview_id": interview.id,
                        "status": "success",
                        "output_file": str(output_file),
                        "turns": result_data["metadata"]["total_turns"],
                        "cost": result_data["metadata"]["estimated_cost"]
                    })
                else:
                    results.append({
                        "interview_id": interview.id,
                        "status": "failed",
                        "error": error_msg
                    })
                
                # Progress update
                if i % 5 == 0:
                    logger.info(f"Processed {i}/{len(txt_files)} interviews")
                
            except Exception as e:
                logger.error(f"Error processing file {txt_file}: {e}")
                results.append({
                    "interview_id": str(txt_file.stem),
                    "status": "error",
                    "error": str(e)
                })
        
        total_time = time.time() - start_time
        
        # Create summary
        summary = {
            "total_interviews": len(txt_files),
            "successful": self.successful_annotations,
            "failed": self.failed_annotations,
            "total_time": total_time,
            "total_cost": self.total_cost,
            "average_cost": self.total_cost / max(self.successful_annotations, 1),
            "results": results
        }
        
        # Save summary
        summary_file = self.output_dir / "batch_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Batch processing complete: {self.successful_annotations}/{len(txt_files)} successful")
        logger.info(f"Total cost: ${self.total_cost:.3f}")
        
        return summary
    
    def create_cost_analysis(self) -> Dict[str, Any]:
        """Create detailed cost analysis for the project."""
        
        # Load a sample interview for cost estimation
        txt_dir = Path("data/processed/interviews_txt")
        txt_files = list(txt_dir.glob("*.txt"))
        
        if not txt_files:
            return {"error": "No interview files found"}
        
        # Use representative interview
        sample_file = sorted(txt_files, key=lambda f: f.stat().st_size)[len(txt_files)//2]
        processor = DocumentProcessor()
        sample_interview = processor.process_interview(sample_file)
        
        # Cost estimates for different models
        models = {
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "gpt-4.1-mini": {"input": 0.40, "output": 1.60}
        }
        
        # Estimate tokens
        input_tokens = len(sample_interview.text.split()) * 1.3 + 1000
        output_tokens = 3000  # Estimated for complete annotation
        
        cost_analysis = {
            "sample_interview": sample_interview.id,
            "estimated_tokens": {
                "input": input_tokens,
                "output": output_tokens
            },
            "cost_per_interview": {},
            "total_project_cost": {}
        }
        
        for model, pricing in models.items():
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            total_per_interview = input_cost + output_cost
            
            cost_analysis["cost_per_interview"][model] = {
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total": total_per_interview
            }
            
            cost_analysis["total_project_cost"][model] = total_per_interview * 37
        
        return cost_analysis


def main():
    """Run batch annotation with cost analysis."""
    
    # Create cost analysis first
    annotator = InstructorBatchAnnotator()
    cost_analysis = annotator.create_cost_analysis()
    
    print("💰 INSTRUCTOR BATCH ANNOTATION COST ANALYSIS")
    print("=" * 60)
    print(f"Sample interview: {cost_analysis['sample_interview']}")
    print(f"Estimated input tokens: {cost_analysis['estimated_tokens']['input']:,.0f}")
    print(f"Estimated output tokens: {cost_analysis['estimated_tokens']['output']:,.0f}")
    print()
    
    print("Cost per interview:")
    for model, costs in cost_analysis["cost_per_interview"].items():
        print(f"  {model}: ${costs['total']:.4f}")
    
    print()
    print("Total project cost (37 interviews):")
    for model, total_cost in cost_analysis["total_project_cost"].items():
        print(f"  {model}: ${total_cost:.2f}")
    
    # Ask user if they want to proceed with actual annotations
    print("\n" + "="*60)
    print("Ready to process interviews with Instructor annotation system.")
    print("Recommended: Start with 3-5 interviews to test the approach.")
    
    response = input("\nProcess interviews? (y/n): ").lower().strip()
    
    if response == 'y':
        max_interviews = input("How many interviews to process (default: 5): ").strip()
        try:
            max_interviews = int(max_interviews) if max_interviews else 5
        except ValueError:
            max_interviews = 5
        
        print(f"\n🚀 Starting batch processing of {max_interviews} interviews...")
        summary = annotator.process_all_interviews(max_interviews=max_interviews)
        
        print(f"\n✅ Batch processing complete!")
        print(f"Successful: {summary['successful']}/{summary['total_interviews']}")
        print(f"Total cost: ${summary['total_cost']:.3f}")
        print(f"Average cost: ${summary['average_cost']:.4f} per interview")
        print(f"Results saved to: {annotator.output_dir}")
    else:
        print("Batch processing cancelled.")


if __name__ == "__main__":
    main()