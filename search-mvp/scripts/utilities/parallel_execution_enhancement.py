"""
Enhancement to enable parallel sub-agent execution

This shows how we could modify the agent to run sub-agents in parallel
"""

import asyncio
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
import time

async def execute_tools_parallel(tool_calls, execute_cli_tool_func):
    """
    Execute multiple tool calls, with spawn_sub_agent calls running in parallel
    """
    # Separate spawn_sub_agent calls from other tools
    spawn_calls = []
    other_calls = []
    
    for tc in tool_calls:
        if tc['tool_name'] == 'spawn_sub_agent':
            spawn_calls.append(tc)
        else:
            other_calls.append(tc)
    
    results = {}
    
    # Execute non-spawn tools sequentially first
    for tc in other_calls:
        result = execute_cli_tool_func(tc['tool_name'], tc['command'], tc['args'])
        results[tc['id']] = result
    
    # Execute spawn_sub_agent calls in parallel
    if spawn_calls:
        print(f"🚀 Spawning {len(spawn_calls)} sub-agents in parallel...")
        
        # Use ThreadPoolExecutor for subprocess calls
        with ThreadPoolExecutor(max_workers=len(spawn_calls)) as executor:
            # Submit all spawn tasks
            future_to_tc = {}
            for tc in spawn_calls:
                future = executor.submit(
                    execute_cli_tool_func,
                    tc['tool_name'],
                    tc['command'], 
                    tc['args']
                )
                future_to_tc[future] = tc
            
            # Collect results as they complete
            for future in future_to_tc:
                tc = future_to_tc[future]
                try:
                    result = future.result(timeout=60)  # 60 second timeout per sub-agent
                    results[tc['id']] = result
                except Exception as e:
                    results[tc['id']] = json.dumps({"error": str(e)})
    
    return results


# Example modification to the agent's tool execution loop:
"""
# In autonomous_research method, replace the sequential execution with:

if hasattr(message, 'tool_calls') and message.tool_calls:
    # Prepare tool calls
    tool_calls_to_execute = []
    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments or '{}')
        tool_config = self.tools[tool_name]
        
        tool_calls_to_execute.append({
            'id': tool_call.id,
            'tool_name': tool_name,
            'command': tool_config["command"],
            'args': tool_args
        })
    
    # Execute tools (parallel for spawn_sub_agent)
    results = await execute_tools_parallel(
        tool_calls_to_execute,
        self.execute_cli_tool
    )
    
    # Process results
    for tool_call in message.tool_calls:
        result = results[tool_call.id]
        # ... rest of processing
"""

# Alternative: Using asyncio.create_subprocess_exec for async execution
async def execute_spawn_sub_agent_async(command):
    """Execute sub-agent asynchronously"""
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()
    
    if proc.returncode != 0:
        return json.dumps({"error": stderr.decode()})
    
    return stdout.decode().strip()


# Demo of time savings:
def demo_time_savings():
    """Show potential time savings with parallel execution"""
    
    print("Time Comparison:")
    print("-" * 40)
    
    # Sequential (current)
    print("Sequential execution (current):")
    print("  Sub-agent 1: 20s")
    print("  Sub-agent 2: 20s")  
    print("  Sub-agent 3: 20s")
    print("  Total: 60s")
    
    print("\nParallel execution (proposed):")
    print("  All 3 sub-agents: ~20s (running simultaneously)")
    print("  Speedup: 3x")
    
    print("\nBenefits:")
    print("  - Faster research for multi-faceted questions")
    print("  - Better resource utilization")
    print("  - Natural for independent sub-questions")

if __name__ == "__main__":
    demo_time_savings()