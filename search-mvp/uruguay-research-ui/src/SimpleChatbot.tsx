import React, { useState } from 'react';

export const SimpleChatbot: React.FC = () => {
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // 1. Call API
      const response = await fetch('http://localhost:8000/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input, provider: 'moonshot' })
      });

      const { job_id } = await response.json();
      console.log('Got job ID:', job_id);

      // 2. Connect WebSocket and wait for result
      const ws = new WebSocket(`ws://localhost:8000/research/${job_id}/stream`);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WS message:', data.type);
        
        if (data.type === 'response_end' || data.type === 'result') {
          const assistantMessage = { 
            role: 'assistant', 
            content: data.data.response || 'No response' 
          };
          setMessages(prev => [...prev, assistantMessage]);
          setLoading(false);
          ws.close();
        }
      };

      ws.onerror = (error) => {
        console.error('WS error:', error);
        setLoading(false);
      };

    } catch (error) {
      console.error('Error:', error);
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      maxWidth: '800px', 
      margin: '0 auto', 
      padding: '20px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <h1>Simple Chatbot Test</h1>
      
      <div style={{ 
        height: '400px', 
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
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: 'center', color: '#666' }}>
            Thinking...
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