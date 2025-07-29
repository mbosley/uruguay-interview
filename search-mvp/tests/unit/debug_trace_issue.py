#!/usr/bin/env python3
"""
Debug trace display issue by running a mock agent test
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_mock_agent():
    """Test the mock agent and monitor WebSocket events"""
    
    # Start research with mock agent
    async with aiohttp.ClientSession() as session:
        # Start research job
        print("🚀 Starting mock research job...")
        async with session.post(
            'http://localhost:8000/research',
            json={
                "question": "What are the main concerns about security in Uruguay?",
                "use_mock": True,
                "max_iterations": 3
            }
        ) as resp:
            result = await resp.json()
            job_id = result['job_id']
            print(f"📋 Job ID: {job_id}")
            
        # Connect to WebSocket
        print("\n🔌 Connecting to WebSocket...")
        async with session.ws_connect(f'ws://localhost:8000/research/{job_id}/stream') as ws:
            print("✅ Connected!")
            print("\n📨 Events received:")
            print("-" * 80)
            
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    event = json.loads(msg.data)
                    
                    # Format the event
                    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    event_type = event.get('type', 'unknown')
                    
                    print(f"\n{ts} | {event_type}")
                    
                    # Show iteration if present
                    if 'iteration' in event:
                        print(f"         | Iteration: {event['iteration']}")
                    
                    # Show relevant data
                    if 'data' in event:
                        data = event['data']
                        if event_type == 'iteration_start':
                            print(f"         | Progress: {data.get('current')}/{data.get('max')}")
                        elif event_type == 'thinking':
                            content = data.get('content', '')[:80]
                            print(f"         | Thinking: {content}...")
                        elif event_type == 'tool_call':
                            print(f"         | Tool: {data.get('tool')}")
                            args = data.get('args', {})
                            for k, v in args.items():
                                print(f"         |   {k}: {v}")
                        elif event_type == 'tool_result':
                            print(f"         | Tool: {data.get('tool')}")
                            if 'metadata' in data and 'preview' in data['metadata']:
                                preview = data['metadata']['preview'][:60]
                                print(f"         | Result: {preview}...")
                        elif event_type in ['response_end', 'result']:
                            response_len = len(data.get('response', ''))
                            print(f"         | Response length: {response_len} chars")
                            if 'sources' in data:
                                print(f"         | Sources: {data['sources']}")
                    
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"❌ WebSocket error: {ws.exception()}")
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    print("\n🔒 WebSocket closed")
                    break
            
            print("-" * 80)
            print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_mock_agent())