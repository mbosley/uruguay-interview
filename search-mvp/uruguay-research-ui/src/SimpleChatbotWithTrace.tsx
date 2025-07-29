import React, { useState } from 'react';

interface TraceItem {
  type: string;
  content: string;
  iteration?: number;
}

export const SimpleChatbotWithTrace: React.FC = () => {
  const [messages, setMessages] = useState<Array<{role: string, content: string, trace?: TraceItem[]}>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentTrace, setCurrentTrace] = useState<TraceItem[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setCurrentTrace([]); // Clear trace for new request

    try {
      // 1. Call API
      const response = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input, provider: 'moonshot' })
      });

      const { job_id } = await response.json();
      console.log('Got job ID:', job_id);

      // 2. Connect WebSocket and collect trace
      // Try 127.0.0.1 instead of localhost
      const wsUrl = `ws://127.0.0.1:8000/research/${job_id}/stream`;
      console.log('Attempting to connect to:', wsUrl);
      
      let ws: WebSocket;
      try {
        ws = new WebSocket(wsUrl);
        console.log('WebSocket object created, readyState:', ws.readyState);
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        setLoading(false);
        return;
      }
      
      const collectedTrace: TraceItem[] = [];
      let messageCount = 0;
      
      // Set up all event handlers immediately
      ws.onopen = () => {
        console.log('✅ WebSocket connected! readyState:', ws.readyState);
      };
      
      ws.onmessage = (event) => {
        messageCount++;
        console.log(`WS message #${messageCount}:`, event.data);
        const data = JSON.parse(event.data);
        console.log('Parsed message:', data.type, data);
        
        // Collect trace events
        switch (data.type) {
          case 'iteration_start':
            collectedTrace.push({
              type: 'iteration',
              content: `Iteration ${data.data.current} of ${data.data.max}`,
              iteration: data.data.current
            });
            break;
            
          case 'thinking':
            collectedTrace.push({
              type: 'thinking',
              content: data.data.content,
              iteration: data.iteration
            });
            break;
            
          case 'tool_call':
            collectedTrace.push({
              type: 'tool_call',
              content: `${data.data.tool}(${JSON.stringify(data.data.args)})`,
              iteration: data.iteration
            });
            break;
            
          case 'tool_result':
            const lastTool = [...collectedTrace].reverse().find(t => t.type === 'tool_call');
            if (lastTool) {
              collectedTrace.push({
                type: 'tool_result',
                content: data.data.metadata?.preview || 'Result received',
                iteration: data.iteration
              });
            }
            break;
        }
        
        // Update current trace in real-time
        setCurrentTrace([...collectedTrace]);
        
        // Handle final response
        if (data.type === 'response_end' || data.type === 'result') {
          const assistantMessage = { 
            role: 'assistant', 
            content: data.data.response || 'No response',
            trace: collectedTrace
          };
          setMessages(prev => [...prev, assistantMessage]);
          setLoading(false);
          setCurrentTrace([]);
          ws.close();
        }
      };

      ws.onerror = (error) => {
        console.error('WS error:', error);
        setLoading(false);
      };
      
      ws.onclose = (event) => {
        console.log('WS closed:', event.code, event.reason);
        if (messageCount === 0) {
          console.error('WebSocket closed without receiving any messages!');
        }
      };
      
      // Add a timeout to detect if WebSocket never connects
      setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket still connecting after 5 seconds!');
          console.log('Current readyState:', ws.readyState);
          console.log('WebSocket states: CONNECTING=0, OPEN=1, CLOSING=2, CLOSED=3');
        }
      }, 5000);

    } catch (error) {
      console.error('Error:', error);
      setLoading(false);
    }
  };

  const renderTrace = (trace: TraceItem[]) => {
    return (
      <div style={{ 
        marginTop: '10px', 
        padding: '10px', 
        backgroundColor: 'rgba(0,0,0,0.1)',
        borderRadius: '4px',
        fontSize: '14px'
      }}>
        <strong>Reasoning Process:</strong>
        {trace.map((item, i) => (
          <div key={i} style={{ 
            marginTop: '5px',
            paddingLeft: item.type === 'iteration' ? '0' : '20px',
            fontWeight: item.type === 'iteration' ? 'bold' : 'normal'
          }}>
            {item.type === 'thinking' && '💭 '}
            {item.type === 'tool_call' && '🔧 '}
            {item.type === 'tool_result' && '✅ '}
            {item.content}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: '0 auto', 
      padding: '20px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <h1>Simple Chatbot with Reasoning Trace</h1>
      
      <div style={{ 
        height: '600px', 
        overflowY: 'auto', 
        border: '1px solid #ccc', 
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px',
        backgroundColor: '#f5f5f5'
      }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ 
            marginBottom: '10px',
            padding: '10px',
            borderRadius: '8px',
            backgroundColor: msg.role === 'user' ? '#007bff' : '#28a745',
            color: 'white',
            marginLeft: msg.role === 'user' ? '20%' : '0',
            marginRight: msg.role === 'assistant' ? '20%' : '0',
          }}>
            <strong>{msg.role}:</strong> {msg.content}
            {msg.trace && renderTrace(msg.trace)}
          </div>
        ))}
        
        {loading && currentTrace.length > 0 && (
          <div style={{ 
            padding: '10px',
            backgroundColor: '#fff',
            borderRadius: '8px',
            border: '2px solid #007bff'
          }}>
            <strong>🔄 Researching...</strong>
            {renderTrace(currentTrace)}
          </div>
        )}
        
        {loading && currentTrace.length === 0 && (
          <div style={{ textAlign: 'center', color: '#666' }}>
            Starting research...
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
          style={{ 
            flex: 1,
            padding: '10px',
            fontSize: '16px',
            borderRadius: '4px',
            border: '1px solid #ccc'
          }}
        />
        <button 
          type="submit" 
          disabled={loading || !input.trim()}
          style={{ 
            padding: '10px 20px',
            fontSize: '16px',
            backgroundColor: loading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
};