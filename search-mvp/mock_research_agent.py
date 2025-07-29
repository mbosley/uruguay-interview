"""
Mock Research Agent for testing frontend integration
Simulates the research process with realistic event emissions
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional, Callable

class MockResearchAgent:
    def __init__(self, event_callback: Optional[Callable] = None):
        self.event_callback = event_callback
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stats = {
            'tool_calls': 0,
            'iterations': 0,
            'start_time': datetime.now(),
            'input_tokens': 0,
            'output_tokens': 0,
            'total_cost': 0.0
        }
    
    async def emit_event(self, event_type: str, data: dict, iteration: int = None):
        """Emit event to callback if available"""
        if self.event_callback:
            event = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            if iteration is not None:
                event["iteration"] = iteration
            await self.event_callback(event)
            # Small delay to simulate real-time feel
            await asyncio.sleep(0.1)
    
    async def autonomous_research(self, research_question: str, max_iterations: int = 3):
        """Simulate research process with realistic event emissions"""
        
        # Start research
        await self.emit_event("progress", {"message": f"Starting research: {research_question}"})
        
        # Simulate 3 iterations
        for iteration in range(1, 4):
            # Emit iteration start
            await self.emit_event("iteration_start", {
                "current": iteration,
                "max": max_iterations
            }, iteration)
            
            # Simulate thinking
            thinking_messages = [
                "I'll start by exploring the corpus to understand the scope of healthcare concerns mentioned by citizens.",
                "Now let me search for specific healthcare themes to identify patterns.",
                "I'll examine specific interviews that mention healthcare issues to extract detailed concerns."
            ]
            
            await self.emit_event("thinking", {
                "content": thinking_messages[iteration - 1]
            }, iteration)
            await asyncio.sleep(0.5)
            
            # Simulate tool calls based on iteration
            if iteration == 1:
                # Get corpus stats
                await self.emit_event("tool_call", {
                    "tool": "get_corpus_stats",
                    "args": {},
                    "id": f"call_{iteration}_1"
                }, iteration)
                await asyncio.sleep(0.8)
                
                await self.emit_event("tool_result", {
                    "tool": "get_corpus_stats",
                    "metadata": {
                        "size": 359,
                        "preview": "37 interviews, 5510 total turns, average 149 turns per interview"
                    }
                }, iteration)
                self.stats['tool_calls'] += 1
                
            elif iteration == 2:
                # List themes
                await self.emit_event("tool_call", {
                    "tool": "list_interview_themes",
                    "args": {},
                    "id": f"call_{iteration}_1"
                }, iteration)
                await asyncio.sleep(1.0)
                
                await self.emit_event("tool_result", {
                    "tool": "list_interview_themes",
                    "metadata": {
                        "size": 11264,
                        "preview": "Found themes: healthcare_access, healthcare_crisis, waiting_times, hospital_infrastructure..."
                    }
                }, iteration)
                self.stats['tool_calls'] += 1
                
                # Search specific themes
                await self.emit_event("tool_call", {
                    "tool": "search_themes",
                    "args": {"keyword": "healthcare"},
                    "id": f"call_{iteration}_2"
                }, iteration)
                await asyncio.sleep(0.8)
                
                await self.emit_event("tool_result", {
                    "tool": "search_themes",
                    "metadata": {
                        "size": 896,
                        "preview": "Found 15 healthcare-related themes across 23 interviews"
                    }
                }, iteration)
                self.stats['tool_calls'] += 1
                
            else:  # iteration 3
                # Get specific interview turns
                await self.emit_event("tool_call", {
                    "tool": "get_interview_turn",
                    "args": {"interview_turn": "071:23"},
                    "id": f"call_{iteration}_1"
                }, iteration)
                await asyncio.sleep(0.8)
                
                await self.emit_event("tool_result", {
                    "tool": "get_interview_turn",
                    "metadata": {
                        "size": 1024,
                        "preview": "Rural resident describes 6-month wait for specialist appointment"
                    }
                }, iteration)
                self.stats['tool_calls'] += 1
                
                # Search interviews
                await self.emit_event("tool_call", {
                    "tool": "search_interviews",
                    "args": {"query": "lista de espera"},
                    "id": f"call_{iteration}_2"
                }, iteration)
                await asyncio.sleep(1.0)
                
                await self.emit_event("tool_result", {
                    "tool": "search_interviews",
                    "metadata": {
                        "size": 2048,
                        "preview": "Found 18 mentions of waiting lists across 12 interviews"
                    }
                }, iteration)
                self.stats['tool_calls'] += 1
            
            # Update stats
            self.stats['iterations'] = iteration
            self.stats['input_tokens'] += 1500
            self.stats['output_tokens'] += 800
            self.stats['total_cost'] += 0.0025
        
        # Emit response generation events
        await self.emit_event("response_start", {})
        await self.emit_event("progress", {"message": "Generating comprehensive summary..."})
        await asyncio.sleep(1.5)
        
        # Generate mock response
        final_response = """# Research Summary: Healthcare Concerns in Uruguay

## Key Findings

**Finding 1: Long Waiting Times**
- Statement: Citizens consistently report excessive waiting times for medical appointments, particularly for specialists
- Evidence: Multiple interviews describe waits of 3-6 months (`071:23`, `084:47`, `089:12`)
- Significance: This represents a critical barrier to healthcare access affecting quality of life

**Finding 2: Rural Healthcare Crisis**
- Statement: Rural areas face severe healthcare infrastructure deficits with closed clinics and doctor shortages
- Evidence: Rural clinic closures mentioned in `071:36` (nearest facility now 50km away), doctor migration patterns in `068:44`
- Significance: Geographic inequality in healthcare access threatens rural community sustainability

**Finding 3: Emergency Service Overload**
- Statement: Emergency departments are overwhelmed due to lack of primary care access
- Evidence: Citizens report using emergency for non-urgent care (`091:78`, `076:23`), staff describe unsustainable workloads (`084:145`)
- Significance: System inefficiency leads to degraded care quality for all patients

## Themes Identified

**Theme 1: Healthcare Infrastructure Abandonment**
- Description: Physical deterioration of facilities and withdrawal of services
- Example: "El centro de salud cerró hace dos años y nunca lo reabrieron" (`071:36`)
- Frequency: Mentioned in 15 interviews

**Theme 2: Healthcare Worker Exhaustion**
- Description: Medical professionals report burnout and consider leaving the profession
- Example: "Los médicos se van porque no aguantan más las condiciones" (`084:89`)
- Frequency: Appears in 8 interviews with healthcare workers

## Patterns and Connections

The healthcare crisis shows clear urban-rural disparities. While urban areas struggle with overwhelming demand (`070:45`, `076:89`), rural communities face complete service withdrawal (`071:36`, `089:34`). This creates a vicious cycle where rural patients travel to cities for care, further straining urban facilities.

The waiting time issue connects directly to specialist shortages. Citizens describe a two-tier system where those who can afford private care skip queues while public system users wait months (`073:56`, `091:23`)."""
        
        # Extract sources
        sources = ["Interview 071", "Interview 084", "Interview 089", "Interview 068", "Interview 091"]
        
        await self.emit_event("response_end", {
            "response": final_response,
            "sources": sources
        })
        
        # Emit final stats
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        await self.emit_event("stats", {
            "duration": duration,
            "iterations": self.stats['iterations'],
            "toolCalls": self.stats['tool_calls'],
            "llmCalls": self.stats['iterations'] + 1,
            "inputTokens": self.stats['input_tokens'],
            "outputTokens": self.stats['output_tokens'],
            "totalCost": self.stats['total_cost']
        })
        
        # Return results
        return {
            "final_response": final_response,
            "tool_calls": [],  # Simplified for mock
            "iterations": self.stats['iterations'],
            "session_id": self.session_id,
            "stats": self.stats
        }


# Test script
async def test_mock_agent():
    """Test the mock agent with event printing"""
    print("Testing Mock Research Agent")
    print("=" * 60)
    
    async def print_event(event):
        print(f"\n[{event['type']}] @ {event.get('iteration', 'N/A')}")
        print(json.dumps(event['data'], indent=2))
    
    agent = MockResearchAgent(event_callback=print_event)
    result = await agent.autonomous_research("What are the main healthcare concerns?")
    
    print("\n" + "=" * 60)
    print("FINAL RESULT:")
    print(f"Response length: {len(result['final_response'])} chars")
    print(f"Total iterations: {result['iterations']}")
    print(f"Total cost: ${result['stats']['total_cost']:.4f}")


if __name__ == "__main__":
    asyncio.run(test_mock_agent())