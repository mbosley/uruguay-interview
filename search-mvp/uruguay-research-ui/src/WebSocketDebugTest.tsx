import React, { useState } from 'react';

export const WebSocketDebugTest: React.FC = () => {
  const [log, setLog] = useState<string[]>([]);

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLog(prev => [...prev, `[${timestamp}] ${msg}`]);
  };

  const testEchoWebSocket = async () => {
    setLog([]);
    addLog('Testing simple echo WebSocket...');
    
    const ws = new WebSocket('ws://localhost:8000/test/echo');
    
    ws.onopen = () => {
      addLog('✅ Echo WebSocket connected!');
      ws.send('Hello from client');
    };
    
    ws.onmessage = (event) => {
      addLog(`📥 Received: ${event.data}`);
    };
    
    ws.onerror = () => addLog('❌ Echo WebSocket error');
    ws.onclose = () => addLog('🔌 Echo WebSocket closed');
    
    // Check state after delays
    [100, 500, 1000, 2000].forEach(delay => {
      setTimeout(() => {
        addLog(`[${delay}ms] Echo WS state: ${ws.readyState}`);
      }, delay);
    });
  };

  const testResearchWebSocket = async () => {
    setLog([]);
    addLog('Testing research WebSocket...');
    
    // First create a job
    const response = await fetch('http://localhost:8000/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: 'test websocket timing', provider: 'moonshot' })
    });
    
    const { job_id } = await response.json();
    addLog(`Got job ID: ${job_id}`);
    
    const ws = new WebSocket(`ws://localhost:8000/research/${job_id}/stream`);
    
    ws.onopen = () => {
      addLog('✅ Research WebSocket connected!');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      addLog(`📥 ${data.type}`);
    };
    
    ws.onerror = () => addLog('❌ Research WebSocket error');
    ws.onclose = () => addLog('🔌 Research WebSocket closed');
    
    // Check state after delays
    [100, 500, 1000, 2000, 5000].forEach(delay => {
      setTimeout(() => {
        addLog(`[${delay}ms] Research WS state: ${ws.readyState}`);
      }, delay);
    });
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>WebSocket Debug Test</h2>
      
      <button 
        onClick={testEchoWebSocket}
        style={{ padding: '10px', marginRight: '10px' }}
      >
        Test Echo WebSocket
      </button>
      
      <button 
        onClick={testResearchWebSocket}
        style={{ padding: '10px' }}
      >
        Test Research WebSocket
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