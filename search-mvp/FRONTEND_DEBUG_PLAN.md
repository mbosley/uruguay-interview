# Frontend Debug Plan

## Issue Summary
The frontend is not creating an assistant message when the user submits a question. Instead, a WebSocket is connecting to an old, cached job and receiving results with no assistant message to display them in.

## Key Observations from Browser Logs

1. **No handleSendMessage execution**: The log "🎯 handleSendMessage called with:" never appears
2. **No assistant message creation**: The log "🤖 Creating assistant message:" never appears  
3. **WebSocket connecting to old job**: WebSocket events are received without any new research being started
4. **Repeated warning**: "⚠️ No currentAssistantMessage to update with result!"

## Debug Steps

### 1. Check if form submission is working
Add these logs to ChatInterface.tsx:
- ✅ Already added: Log in handleSubmit to verify form submission
- ✅ Already added: Log when calling onSendMessage

### 2. Check if App.tsx is receiving the message
- ✅ Already added: Log at start of handleSendMessage

### 3. Find where the WebSocket is being created
Look for:
- Any automatic WebSocket connections on page load
- Cached job IDs being used
- WebSocket reconnection logic that might be using old jobs

### 4. Test with clean state
1. Clear browser cache and local storage
2. Restart all services
3. Open browser console
4. Submit a new question
5. Watch for the sequence:
   - "🚀 handleSubmit called"
   - "📤 Calling onSendMessage"
   - "🎯 handleSendMessage called"
   - "🤖 Creating assistant message"

## Potential Causes

1. **Event handler not connected**: The onSendMessage prop might not be properly connected
2. **State issue**: Something might be preventing the form from working properly
3. **WebSocket auto-reconnect**: The WebSocket might be automatically reconnecting to old jobs
4. **Browser caching**: The browser might be caching WebSocket connections

## Next Steps

1. Have the user clear browser cache and test again
2. Check if the ChatInterface is receiving the correct props
3. Add more detailed logging around WebSocket creation
4. Test with the debug components enabled