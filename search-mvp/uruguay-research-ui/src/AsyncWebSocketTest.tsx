import React, { useState } from 'react';

export const AsyncWebSocketTest: React.FC = () => {
  const [log, setLog] = useState<string[]>([]);

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLog(prev => [...prev, `[${timestamp}] ${msg}`]);
    console.log(msg);
  };

  const testAsyncFlow = async () => {
    setLog([]);
    addLog('Starting async test...');
    
    try {
      // Start the API call but DON'T await it yet
      addLog('Starting API call (not awaiting)...');
      const apiPromise = fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: 'test async flow', provider: 'moonshot' })
      }).then(r => r.json());
      
      // Give the API call a moment to start
      await new Promise(resolve => setTimeout(resolve, 50));
      
      // Now await the result
      addLog('Awaiting API response...');
      const { job_id } = await apiPromise;
      addLog(`Got job ID: ${job_id}`);
      
      // Create WebSocket in a separate async function
      const connectWebSocket = async () => {
        addLog('Creating WebSocket in async function...');
        const ws = new WebSocket(`ws://localhost:8000/research/${job_id}/stream`);
        
        ws.onopen = () => addLog('✅ WebSocket connected!');
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          addLog(`📥 ${data.type}`);
        };
        ws.onerror = () => addLog('❌ WebSocket error');
        ws.onclose = () => addLog('🔌 WebSocket closed');
        
        return ws;
      };
      
      // Start WebSocket connection without blocking
      connectWebSocket().then(ws => {
        addLog('WebSocket promise resolved');
      });
      
      // Also try creating WebSocket directly after a microtask
      Promise.resolve().then(() => {
        addLog('Creating WebSocket in microtask...');
        const ws2 = new WebSocket(`ws://localhost:8000/research/${job_id}/stream`);
        ws2.onopen = () => addLog('✅ WebSocket 2 connected!');
      });
      
      // And try with setTimeout 0
      setTimeout(() => {
        addLog('Creating WebSocket in setTimeout...');
        const ws3 = new WebSocket(`ws://localhost:8000/research/${job_id}/stream`);
        ws3.onopen = () => addLog('✅ WebSocket 3 connected!');
      }, 0);
      
    } catch (error) {
      addLog(`Error: ${error}`);
    }
  };

  const testSyncFlow = async () => {
    setLog([]);
    addLog('Starting sync test (normal flow)...');
    
    try {
      const response = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: 'test sync flow', provider: 'moonshot' })
      });
      
      const { job_id } = await response.json();
      addLog(`Got job ID: ${job_id}`);
      
      const ws = new WebSocket(`ws://localhost:8000/research/${job_id}/stream`);
      ws.onopen = () => addLog('✅ WebSocket connected!');
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addLog(`📥 ${data.type}`);
      };
      
    } catch (error) {
      addLog(`Error: ${error}`);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>Async WebSocket Connection Test</h2>
      
      <button 
        onClick={testAsyncFlow}
        style={{ padding: '10px', marginRight: '10px' }}
      >
        Test Async Flow
      </button>
      
      <button 
        onClick={testSyncFlow}
        style={{ padding: '10px' }}
      >
        Test Sync Flow (Normal)
      </button>
      
      <div style={{
        marginTop: '20px',
        padding: '10px',
        border: '1px solid #ccc',
        height: '500px',
        overflow: 'auto',
        backgroundColor: '#f0f0f0'
      }}>
        {log.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
    </div>
  );
};