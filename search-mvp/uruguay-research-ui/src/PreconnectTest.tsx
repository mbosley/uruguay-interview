import React, { useState } from 'react';

export const PreconnectTest: React.FC = () => {
  const [log, setLog] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string>('');

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLog(prev => [...prev, `[${timestamp}] ${msg}`]);
  };

  const testPreconnect = async () => {
    setLog([]);
    addLog('Starting test...');
    
    try {
      // 1. Create a dummy WebSocket to "warm up" the connection
      addLog('Creating dummy WebSocket...');
      const dummyWs = new WebSocket('ws://localhost:8000/dummy');
      dummyWs.onerror = () => addLog('Dummy WS error (expected)');
      dummyWs.onclose = () => addLog('Dummy WS closed');
      
      // Give it a moment
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 2. Now create the real job
      addLog('Creating research job...');
      const response = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: 'test preconnect', provider: 'moonshot' })
      });
      
      const { job_id } = await response.json();
      setJobId(job_id);
      addLog(`Got job ID: ${job_id}`);
      
      // 3. Immediately connect WebSocket
      const wsUrl = `ws://localhost:8000/research/${job_id}/stream`;
      addLog(`Connecting to: ${wsUrl}`);
      
      const ws = new WebSocket(wsUrl);
      let connected = false;
      
      ws.onopen = () => {
        connected = true;
        addLog('✅ WebSocket connected!');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addLog(`📥 ${data.type}`);
        
        if (data.type === 'response_end') {
          addLog('🏁 Research complete!');
          ws.close();
        }
      };
      
      ws.onerror = () => addLog('❌ WebSocket error');
      ws.onclose = () => addLog('🔌 WebSocket closed');
      
      // Monitor connection state
      for (let i = 0; i < 10; i++) {
        await new Promise(resolve => setTimeout(resolve, 500));
        if (!connected) {
          addLog(`Still connecting... (${i * 0.5}s)`);
        } else {
          break;
        }
      }
      
    } catch (error) {
      addLog(`Error: ${error}`);
    }
  };

  const testWithoutPreconnect = async () => {
    setLog([]);
    addLog('Starting test without preconnect...');
    
    try {
      // Just do the normal flow
      const response = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: 'test normal', provider: 'moonshot' })
      });
      
      const { job_id } = await response.json();
      setJobId(job_id);
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
      <h2>WebSocket Preconnect Test</h2>
      
      <button 
        onClick={testPreconnect}
        style={{ padding: '10px', marginRight: '10px' }}
      >
        Test WITH Preconnect
      </button>
      
      <button 
        onClick={testWithoutPreconnect}
        style={{ padding: '10px' }}
      >
        Test WITHOUT Preconnect
      </button>
      
      <div style={{ marginTop: '20px' }}>
        <strong>Job ID:</strong> {jobId || 'None'}
      </div>
      
      <div style={{
        marginTop: '20px',
        padding: '10px',
        border: '1px solid #ccc',
        height: '400px',
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