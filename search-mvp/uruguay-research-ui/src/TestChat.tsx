import React, { useState, useEffect } from 'react';
import { researchAPI } from './services/api';
import { ResearchWebSocket } from './services/websocket';

export const TestChat: React.FC = () => {
  const [status, setStatus] = useState<string>('Ready');
  const [jobId, setJobId] = useState<string>('');
  const [events, setEvents] = useState<string[]>([]);
  const [error, setError] = useState<string>('');

  const handleTestClick = async () => {
    try {
      setStatus('Starting research...');
      setEvents([]);
      setError('');
      
      // 1. Call API
      console.log('📞 Calling API...');
      const startTime = Date.now();
      const { job_id } = await researchAPI.startResearch('test question');
      const apiTime = Date.now() - startTime;
      
      console.log(`✅ Got job_id: ${job_id} in ${apiTime}ms`);
      setJobId(job_id);
      setStatus(`Got job ID: ${job_id} (${apiTime}ms)`);
      
      // 2. Connect WebSocket
      console.log('🔌 Connecting WebSocket...');
      const ws = new ResearchWebSocket(job_id);
      
      ws.connect({
        onConnect: () => {
          console.log('✅ WebSocket connected');
          setStatus('WebSocket connected');
        },
        onMessage: (message) => {
          console.log('📥 Message:', message);
          setEvents(prev => [...prev, `${message.type}: ${JSON.stringify(message.data).substring(0, 100)}...`]);
          
          if (message.type === 'result' || message.type === 'response_end') {
            setStatus('Research complete!');
          }
        },
        onError: (err) => {
          console.error('❌ Error:', err);
          setError('WebSocket error');
        },
        onDisconnect: () => {
          console.log('🔌 Disconnected');
        }
      });
      
    } catch (err) {
      console.error('❌ Error:', err);
      setError(String(err));
      setStatus('Error');
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>WebSocket Test</h2>
      
      <button 
        onClick={handleTestClick}
        style={{ 
          padding: '10px 20px', 
          fontSize: '16px',
          background: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Test Research Flow
      </button>
      
      <div style={{ marginTop: '20px' }}>
        <h3>Status: {status}</h3>
        {jobId && <p>Job ID: {jobId}</p>}
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      </div>
      
      <div style={{ marginTop: '20px' }}>
        <h3>Events:</h3>
        <div style={{ 
          background: '#f0f0f0', 
          padding: '10px',
          maxHeight: '300px',
          overflow: 'auto'
        }}>
          {events.length === 0 ? (
            <p>No events yet</p>
          ) : (
            events.map((event, i) => (
              <div key={i} style={{ marginBottom: '5px' }}>
                {event}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};