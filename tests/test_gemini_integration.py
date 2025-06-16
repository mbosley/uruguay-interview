"""
Test script for Google Gemini integration in the annotation engine.
"""
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.annotation.annotation_engine import AnnotationEngine
from src.pipeline.annotation.prompt_manager import PromptManager


def test_gemini_initialization():
    """Test that Gemini provider initializes correctly."""
    print("Testing Gemini initialization...")
    
    try:
        engine = AnnotationEngine(model_provider="gemini")
        print(f"✓ Successfully initialized Gemini engine with model: {engine.model_name}")
        print(f"  Model provider: {engine.model_provider}")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize Gemini engine: {e}")
        return False


def test_cost_calculation():
    """Test that cost calculation includes Gemini pricing."""
    print("\nTesting cost calculation...")
    
    try:
        from src.pipeline.ingestion.document_processor import InterviewDocument
        
        # Create a mock interview
        mock_interview = InterviewDocument(
            id="test_001",
            date="2025-01-01",
            time="10:00",
            location="Montevideo",
            department=None,
            participant_count=3,
            text="This is a test interview " * 100,  # ~100 words
            metadata={},
            file_path="test.txt"
        )
        
        engine = AnnotationEngine(model_provider="gemini")
        costs = engine.calculate_annotation_cost(mock_interview)
        
        if "gemini_20_flash" in costs:
            print(f"✓ Gemini cost calculation successful:")
            
            # Show all Gemini models
            print(f"\n  Gemini model pricing comparison:")
            for model_name, cost_data in costs.items():
                if model_name.startswith("gemini"):
                    print(f"  - {model_name}: ${cost_data['total_cost']:.6f}")
                    if "note" in cost_data:
                        print(f"    ({cost_data['note']})")
            
            # Compare with other providers
            gemini_flash = costs.get("gemini_20_flash", {}).get("total_cost", 0)
            openai_gpt4o = costs.get("openai_gpt4o", {}).get("total_cost", 0)
            openai_mini = costs.get("openai_gpt4o_mini", {}).get("total_cost", 0)
            openai_nano = costs.get("openai_gpt41_nano", {}).get("total_cost", 0)
            anthropic_cost = costs.get("anthropic_claude3", {}).get("total_cost", 0)
            
            print(f"\n  Provider comparison (per interview):")
            print(f"  - GPT-4.1-nano: ${openai_nano:.6f} (OpenAI's cheapest)")
            print(f"  - Gemini 2.0 Flash: ${gemini_flash:.6f} (Google's fastest)")
            print(f"  - GPT-4o-mini: ${openai_mini:.6f} (OpenAI's balanced)")
            print(f"  - GPT-4o: ${openai_gpt4o:.6f} ({openai_gpt4o/gemini_flash:.1f}x more than Gemini)")
            print(f"  - Claude 3 Opus: ${anthropic_cost:.4f} ({anthropic_cost/gemini_flash:.0f}x more than Gemini)")
            
            # Project cost for 5000 interviews
            print(f"\n  Cost projection for 5,000 interviews:")
            print(f"  - GPT-4.1-nano: ${openai_nano * 5000:.2f}")
            print(f"  - Gemini 2.0 Flash: ${gemini_flash * 5000:.2f}")
            print(f"  - GPT-4o-mini: ${openai_mini * 5000:.2f}")
            print(f"  - GPT-4o: ${openai_gpt4o * 5000:.2f}")
            print(f"  - Claude 3 Opus: ${anthropic_cost * 5000:.2f}")
            
            return True
        else:
            print("✗ Gemini pricing not found in cost calculation")
            return False
            
    except Exception as e:
        print(f"✗ Failed to calculate costs: {e}")
        return False


def test_gemini_models():
    """Test different Gemini model configurations."""
    print("\nTesting Gemini model variants...")
    
    models = [
        ("gemini-2.0-flash", "Latest, most cost-effective"),
        ("gemini-2.5-flash-preview", "Preview with free tier"),
        ("gemini-2.5-pro-preview", "Preview with 200k context"),
        ("gemini-1.5-pro", "2M context window"),
        ("gemini-1.5-flash", "Legacy flash model")
    ]
    
    for model, description in models:
        try:
            engine = AnnotationEngine(model_provider="gemini", model_name=model)
            print(f"✓ {model}: {description}")
        except Exception as e:
            print(f"✗ Failed to configure model {model}: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Google Gemini Integration Tests")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n⚠️  Warning: GOOGLE_API_KEY environment variable not set")
        print("   Set it with: export GOOGLE_API_KEY='your-api-key'")
        print("   Get a key from: https://makersuite.google.com/app/apikey")
    
    # Run tests
    test_gemini_initialization()
    test_cost_calculation()
    test_gemini_models()
    
    print("\n" + "=" * 60)
    print("Tests complete!")
    
    if os.getenv("GOOGLE_API_KEY"):
        print("\n✓ Ready to use Gemini for annotation!")
        print("  Example: engine = AnnotationEngine(model_provider='gemini')")
    else:
        print("\n⚠️  Remember to set GOOGLE_API_KEY before using Gemini")


if __name__ == "__main__":
    main()