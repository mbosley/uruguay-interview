#!/usr/bin/env python3
"""
Compare performance between Moonshot and Groq providers
"""

import asyncio
import time
import os
from dotenv import load_dotenv
from interview_research_agent_improved import InterviewResearchAgent

load_dotenv()

async def test_provider(provider_name, question, max_iterations=3):
    """Test a provider with a given question"""
    
    print(f"\n{'='*60}")
    print(f"Testing {provider_name.upper()}")
    print(f"{'='*60}")
    
    try:
        agent = InterviewResearchAgent(
            provider=provider_name,
            verbose=True,
            research_mode=False
        )
        
        start_time = time.time()
        results = await agent.autonomous_research(question, max_iterations=max_iterations)
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"\n✅ {provider_name.upper()} Results:")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Iterations: {results['iterations']}")
        print(f"   Tool calls: {results['tool_calls_count']}")
        
        # Estimate tokens from response
        response_words = len(results['final_response'].split())
        estimated_tokens = response_words * 1.5
        tokens_per_sec = estimated_tokens / duration
        
        print(f"   Estimated tokens/sec: {tokens_per_sec:.1f}")
        
        return {
            "provider": provider_name,
            "duration": duration,
            "iterations": results['iterations'],
            "tool_calls": results['tool_calls_count'],
            "tokens_per_sec": tokens_per_sec
        }
        
    except Exception as e:
        print(f"❌ Error with {provider_name}: {e}")
        return None

async def main():
    """Compare providers"""
    
    print("🏁 Provider Performance Comparison")
    print("=" * 60)
    
    # Check which providers are available
    available = []
    if os.getenv("MOONSHOT_API_KEY"):
        available.append("moonshot")
    if os.getenv("GROQ_API_KEY"):
        available.append("groq")
    
    if len(available) < 2:
        print("❌ Need both MOONSHOT_API_KEY and GROQ_API_KEY to compare")
        return
    
    # Test question
    question = "What are the top 3 security concerns mentioned by citizens? Provide specific examples."
    
    print(f"\n📋 Test Question: {question}")
    print(f"🔧 Max Iterations: 3")
    
    # Test each provider
    results = []
    for provider in available:
        result = await test_provider(provider, question, max_iterations=3)
        if result:
            results.append(result)
    
    # Compare results
    if len(results) == 2:
        print(f"\n{'='*60}")
        print("📊 COMPARISON SUMMARY")
        print(f"{'='*60}")
        
        moonshot_result = next((r for r in results if r["provider"] == "moonshot"), None)
        groq_result = next((r for r in results if r["provider"] == "groq"), None)
        
        if moonshot_result and groq_result:
            speedup = moonshot_result["duration"] / groq_result["duration"]
            print(f"\n🚀 Groq is {speedup:.1f}x faster than Moonshot")
            print(f"   Moonshot: {moonshot_result['duration']:.1f}s")
            print(f"   Groq: {groq_result['duration']:.1f}s")
            print(f"\n📈 Tokens/sec comparison:")
            print(f"   Moonshot: {moonshot_result['tokens_per_sec']:.1f} tok/s")
            print(f"   Groq: {groq_result['tokens_per_sec']:.1f} tok/s")

if __name__ == "__main__":
    asyncio.run(main())