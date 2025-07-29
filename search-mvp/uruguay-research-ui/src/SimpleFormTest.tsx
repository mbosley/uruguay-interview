import React, { useState } from 'react';

export const SimpleFormTest: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<string[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('🚀 Form submitted with:', input);
    if (input.trim()) {
      const message = `Submitted: ${input} at ${new Date().toLocaleTimeString()}`;
      setMessages(prev => [...prev, message]);
      console.log('✅ Added message:', message);
      setInput('');
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h2>Simple Form Test</h2>
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type something..."
          style={{
            padding: '10px',
            fontSize: '16px',
            width: '300px',
            marginRight: '10px'
          }}
        />
        <button 
          type="submit"
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
          Submit
        </button>
      </form>

      <div style={{ marginTop: '20px' }}>
        <h3>Messages:</h3>
        {messages.length === 0 ? (
          <p>No messages yet</p>
        ) : (
          <ul>
            {messages.map((msg, i) => (
              <li key={i}>{msg}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};