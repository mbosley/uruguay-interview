import React, { useState } from 'react';

export const MinimalTrace: React.FC = () => {
  const [trace, setTrace] = useState<string[]>([]);
  const [jobId, setJobId] = useState<string>('');
  const [wsStatus, setWsStatus] = useState<string>('Not connected');

  const startResearch = async () => {
    setTrace([]);
    setWsStatus('Starting...');
    
    // 1. Get job ID
    const response = await fetch('http://localhost:8000/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: 'test minimal trace', provider: 'moonshot' })
    });
    
    const { job_id } = await response.json();
    setJobId(job_id);
    setTrace(prev => [...prev, `Got job ID: ${job_id}`]);
    
    // 2. Connect WebSocket - MINIMAL setup
    const ws = new WebSocket(`ws://localhost:8000/research/${job_id}/stream`);
    
    ws.onopen = () => {
      setWsStatus('Connected!');
      setTrace(prev => [...prev, '✅ WebSocket connected']);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const timestamp = new Date().toLocaleTimeString();
        
        // Just log everything
        setTrace(prev => [...prev, `[${timestamp}] ${data.type}: ${JSON.stringify(data.data || {}).substring(0, 100)}...`]);
        
        // Close on completion
        if (data.type === 'response_end' || data.type === 'error') {
          ws.close();
          setWsStatus('Completed');
        }
      } catch (e) {
        setTrace(prev => [...prev, `Error parsing: ${event.data}`]);
      }
    };
    
    ws.onerror = () => {
      setWsStatus('Error!');
      setTrace(prev => [...prev, '❌ WebSocket error']);
    };
    
    ws.onclose = () => {
      setWsStatus('Closed');
      setTrace(prev => [...prev, '🔌 WebSocket closed']);
    };
    
    // Check connection status after delays
    [100, 500, 1000, 2000, 5000].forEach(delay => {
      setTimeout(() => {
        setTrace(prev => [...prev, `[${delay}ms] WebSocket state: ${ws.readyState} (0=CONNECTING, 1=OPEN)`]);
      }, delay);
    });
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>Minimal WebSocket Trace Test</h2>
      <button 
        onClick={startResearch}
        style={{
          padding: '10px 20px',
          fontSize: '16px',
          marginBottom: '20px'
        }}
      >
        Start Research
      </button>
      
      <div>
        <strong>Job ID:</strong> {jobId || 'None'}<br/>
        <strong>WS Status:</strong> {wsStatus}<br/>
      </div>
      
      <div style={{
        marginTop: '20px',
        padding: '10px',
        border: '1px solid #ccc',
        height: '400px',
        overflow: 'auto',
        backgroundColor: '#f0f0f0'
      }}>
        <h3>Trace Log:</h3>
        {trace.map((line, i) => (
          <div key={i} style={{ marginBottom: '5px' }}>
            {line}
          </div>
        ))}
      </div>
    </div>
  );
};