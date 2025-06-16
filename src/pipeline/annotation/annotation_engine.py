"""
AI-powered annotation engine for interview analysis.
"""
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import logging
import time

from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai

from src.pipeline.ingestion.document_processor import InterviewDocument
from src.pipeline.annotation.prompt_manager import PromptManager
from src.config.config_loader import get_config

logger = logging.getLogger(__name__)


class AnnotationEngine:
    """Generates AI-powered annotations for interviews using XML schema."""
    
    def __init__(
        self, 
        prompt_manager: Optional[PromptManager] = None,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        config = None
    ):
        """
        Initialize annotation engine.
        
        Args:
            prompt_manager: PromptManager instance (creates default if None)
            model_provider: 'openai', 'anthropic', or 'gemini' (overrides config)
            model_name: Specific model to use (overrides config)
            config: Configuration object (uses global config if None)
        """
        # Load configuration
        self.config = config or get_config()
        
        # Use provided values or fall back to config
        self.model_provider = (model_provider or self.config.ai.provider).lower()
        self.model_name = model_name or self.config.ai.model
        
        # Initialize prompt manager
        self.prompt_manager = prompt_manager or PromptManager(
            prompt_file=self.config.annotation.prompt_file
        )
        
        # Get API key from config loader
        from src.config.config_loader import ConfigLoader
        loader = ConfigLoader()
        api_key = loader.get_api_key(self.model_provider)
        
        if not api_key:
            raise ValueError(f"No API key found for provider: {self.model_provider}")
        
        # Initialize AI client
        if self.model_provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif self.model_provider == "anthropic":
            self.client = Anthropic(api_key=api_key)
        elif self.model_provider == "gemini":
            genai.configure(api_key=api_key)
            self.client = None  # Gemini uses module-level functions
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")
        
        logger.info(f"Initialized {self.model_provider} annotation engine with model {self.model_name}")
    
    def annotate_interview(
        self, 
        interview: InterviewDocument,
        max_retries: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Tuple[ET.Element, Dict[str, Any]]:
        """
        Generate AI annotation for an interview.
        
        Args:
            interview: Processed interview document
            max_retries: Maximum retry attempts (uses config default if None)
            temperature: AI temperature setting (uses config default if None)
            
        Returns:
            Tuple of (XML annotation, processing metadata)
        """
        # Use config defaults if not specified
        max_retries = max_retries or self.config.ai.max_retries
        temperature = temperature or self.config.ai.temperature
        
        start_time = time.time()
        
        # Create annotation prompt
        interview_metadata = {
            "id": interview.id,
            "date": interview.date,
            "location": interview.location,
            "department": interview.department,
            "participant_count": interview.participant_count
        }
        
        prompt = self.prompt_manager.create_annotation_prompt(
            interview.text, 
            interview_metadata
        )
        
        # Try to get annotation with retries
        annotation = None
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Annotation attempt {attempt + 1} for interview {interview.id}")
                
                # Call appropriate AI provider
                if self.model_provider == "openai":
                    annotation_xml = self._call_openai(prompt, temperature)
                elif self.model_provider == "anthropic":
                    annotation_xml = self._call_anthropic(prompt, temperature)
                else:
                    annotation_xml = self._call_gemini(prompt, temperature)
                
                # Parse and validate
                annotation = self.prompt_manager.parse_annotation_response(annotation_xml)
                is_valid, errors = self.prompt_manager.validate_annotation(annotation)
                
                if not is_valid:
                    logger.warning(f"Validation errors: {errors}")
                    if attempt < max_retries - 1:
                        # Try to fix errors in next attempt
                        prompt = self._create_correction_prompt(prompt, errors)
                        continue
                
                # Success!
                break
                
            except Exception as e:
                logger.error(f"Annotation attempt {attempt + 1} failed: {e}")
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        if annotation is None:
            raise RuntimeError(f"Failed to annotate after {max_retries} attempts: {last_error}")
        
        # Create processing metadata
        processing_metadata = {
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "timestamp": datetime.now().isoformat(),
            "processing_time": time.time() - start_time,
            "attempts": attempt + 1,
            "temperature": temperature,
            "interview_word_count": len(interview.text.split()),
            "confidence": self._extract_confidence(annotation)
        }
        
        # Add processing metadata to annotation
        self._add_processing_metadata(annotation, processing_metadata)
        
        return annotation, processing_metadata
    
    def _call_openai(self, prompt: str, temperature: float) -> str:
        """Call OpenAI API for annotation."""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert qualitative researcher specializing in citizen consultations. You follow annotation schemas precisely and output valid XML."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=8000  # Generous limit for detailed annotations
        )
        
        return response.choices[0].message.content
    
    def _call_anthropic(self, prompt: str, temperature: float) -> str:
        """Call Anthropic API for annotation."""
        response = self.client.messages.create(
            model=self.model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=8000,
            system="You are an expert qualitative researcher specializing in citizen consultations. You follow annotation schemas precisely and output valid XML."
        )
        
        return response.content[0].text
    
    def _call_gemini(self, prompt: str, temperature: float) -> str:
        """Call Google Gemini API for annotation."""
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction="You are an expert qualitative researcher specializing in citizen consultations. You follow annotation schemas precisely and output valid XML."
        )
        
        # Configure generation settings
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=8000,
        )
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return response.text
    
    def _create_correction_prompt(self, original_prompt: str, errors: List[str]) -> str:
        """Create a prompt to correct validation errors."""
        error_text = "\n".join(f"- {error}" for error in errors)
        
        correction_prompt = f"""The previous annotation had validation errors:

{error_text}

Please provide a corrected annotation that addresses these errors.

{original_prompt}"""
        
        return correction_prompt
    
    def _extract_confidence(self, annotation: ET.Element) -> float:
        """Extract overall confidence score from annotation."""
        confidence_elem = annotation.find(".//overall_confidence")
        if confidence_elem is not None and confidence_elem.text:
            try:
                return float(confidence_elem.text)
            except ValueError:
                pass
        return 0.0
    
    def _add_processing_metadata(self, annotation: ET.Element, metadata: Dict[str, Any]) -> None:
        """Add processing metadata to annotation XML."""
        processing_elem = ET.SubElement(annotation, "processing_metadata")
        
        for key, value in metadata.items():
            elem = ET.SubElement(processing_elem, key)
            elem.text = str(value)
    
    def batch_annotate(
        self,
        interviews: List[InterviewDocument],
        output_dir: Optional[str] = None,
        max_concurrent: int = 1
    ) -> List[Tuple[str, bool, Optional[str]]]:
        """
        Annotate multiple interviews in batch.
        
        Args:
            interviews: List of interview documents
            output_dir: Directory to save annotations (optional)
            max_concurrent: Maximum concurrent API calls (1 for now)
            
        Returns:
            List of (interview_id, success, error_message) tuples
        """
        results = []
        
        for interview in interviews:
            try:
                logger.info(f"Processing interview {interview.id}")
                
                # Annotate
                annotation, metadata = self.annotate_interview(interview)
                
                # Save if output directory provided
                if output_dir:
                    output_path = os.path.join(
                        output_dir, 
                        f"{interview.id}_annotation.xml"
                    )
                    tree = ET.ElementTree(annotation)
                    tree.write(output_path, encoding="utf-8", xml_declaration=True)
                    logger.info(f"Saved annotation to {output_path}")
                
                results.append((interview.id, True, None))
                
            except Exception as e:
                logger.error(f"Failed to annotate interview {interview.id}: {e}")
                results.append((interview.id, False, str(e)))
        
        # Summary
        success_count = sum(1 for _, success, _ in results if success)
        logger.info(f"Batch annotation complete: {success_count}/{len(interviews)} successful")
        
        return results
    
    def calculate_annotation_cost(self, interview: InterviewDocument) -> Dict[str, float]:
        """
        Estimate the cost of annotating an interview.
        
        Returns cost estimates for different providers.
        """
        # Rough token estimates
        prompt_tokens = len(interview.text.split()) * 1.5  # XML overhead
        output_tokens = 2000  # Typical annotation size
        
        costs = {}
        
        # OpenAI pricing (multiple models) - prices per 1M tokens
        # GPT-4o (most capable general model)
        costs["openai_gpt4o"] = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "prompt_cost": (prompt_tokens / 1_000_000) * 2.50,  # $2.50 per 1M tokens
            "output_cost": (output_tokens / 1_000_000) * 10.00,  # $10.00 per 1M tokens
            "total_cost": ((prompt_tokens / 1_000_000) * 2.50) + ((output_tokens / 1_000_000) * 10.00)
        }
        
        # GPT-4o-mini (cost-effective)
        costs["openai_gpt4o_mini"] = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "prompt_cost": (prompt_tokens / 1_000_000) * 0.15,  # $0.15 per 1M tokens
            "output_cost": (output_tokens / 1_000_000) * 0.60,  # $0.60 per 1M tokens
            "total_cost": ((prompt_tokens / 1_000_000) * 0.15) + ((output_tokens / 1_000_000) * 0.60)
        }
        
        # GPT-4.1-nano (cheapest)
        costs["openai_gpt41_nano"] = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "prompt_cost": (prompt_tokens / 1_000_000) * 0.10,  # $0.10 per 1M tokens
            "output_cost": (output_tokens / 1_000_000) * 0.40,  # $0.40 per 1M tokens
            "total_cost": ((prompt_tokens / 1_000_000) * 0.10) + ((output_tokens / 1_000_000) * 0.40)
        }
        
        # Anthropic pricing (Claude 3 Opus)
        costs["anthropic_claude3"] = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "prompt_cost": (prompt_tokens / 1000) * 0.015,  # $0.015 per 1K tokens
            "output_cost": (output_tokens / 1000) * 0.075,  # $0.075 per 1K tokens
            "total_cost": ((prompt_tokens / 1000) * 0.015) + ((output_tokens / 1000) * 0.075)
        }
        
        # Google Gemini pricing (multiple models)
        # Gemini 2.0 Flash - Most cost-effective
        costs["gemini_20_flash"] = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "prompt_cost": (prompt_tokens / 1_000_000) * 0.10,  # $0.10 per 1M tokens
            "output_cost": (output_tokens / 1_000_000) * 0.40,  # $0.40 per 1M tokens
            "total_cost": ((prompt_tokens / 1_000_000) * 0.10) + ((output_tokens / 1_000_000) * 0.40)
        }
        
        # Gemini 2.5 Flash Preview - Free tier available
        costs["gemini_25_flash_preview"] = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "prompt_cost": (prompt_tokens / 1_000_000) * 0.15,  # $0.15 per 1M tokens
            "output_cost": (output_tokens / 1_000_000) * 0.60,  # $0.60 per 1M tokens (base rate)
            "total_cost": ((prompt_tokens / 1_000_000) * 0.15) + ((output_tokens / 1_000_000) * 0.60),
            "note": "Free tier available in Google AI Studio"
        }
        
        # Gemini 1.5 Pro - Higher context window (2M tokens)
        costs["gemini_15_pro"] = {
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "prompt_cost": (prompt_tokens / 1_000_000) * 1.25,  # $1.25 per 1M tokens (base rate)
            "output_cost": (output_tokens / 1_000_000) * 5.00,  # $5.00 per 1M tokens (base rate)
            "total_cost": ((prompt_tokens / 1_000_000) * 1.25) + ((output_tokens / 1_000_000) * 5.00)
        }
        
        return costs


if __name__ == "__main__":
    # Test annotation engine
    from src.pipeline.ingestion.document_processor import DocumentProcessor
    
    # Initialize components
    processor = DocumentProcessor()
    engine = AnnotationEngine(model_provider="openai")
    
    # Test with a sample file if available
    sample_file = "data/processed/interviews_txt/20250528_0900_058.txt"
    if os.path.exists(sample_file):
        from pathlib import Path
        
        # Process document
        interview = processor.process_interview(Path(sample_file))
        print(f"Processing interview {interview.id}")
        print(f"Word count: {len(interview.text.split())}")
        
        # Calculate cost
        costs = engine.calculate_annotation_cost(interview)
        print("\nEstimated annotation costs:")
        for provider, cost_data in costs.items():
            print(f"\n{provider}:")
            print(f"  Total cost: ${cost_data['total_cost']:.3f}")
            print(f"  Tokens: {cost_data['prompt_tokens']:.0f} prompt + {cost_data['output_tokens']:.0f} output")
    else:
        print(f"Sample file not found: {sample_file}")