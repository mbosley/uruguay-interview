# Frontend Rewrite Proposal

## Core Principles

1. **Single Source of Truth**: One state object for the entire research session
2. **Event-Driven Architecture**: Clear event contracts with TypeScript types
3. **Separation of Concerns**: WebSocket, state management, and UI in separate layers
4. **State Machine**: Explicit states for the research flow

## Proposed Architecture

### 1. Research State Machine

```typescript
type ResearchState = 
  | { type: 'idle' }
  | { type: 'connecting'; jobId: string }
  | { type: 'researching'; jobId: string; trace: ResearchTrace[] }
  | { type: 'completed'; jobId: string; response: string; trace: ResearchTrace[] }
  | { type: 'error'; error: string };
```

### 2. Single Message Store

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    jobId?: string;
    trace?: ResearchTrace[];
    sources?: string[];
    stats?: ResearchStats;
    state: 'pending' | 'researching' | 'completed' | 'error';
  };
}
```

### 3. Event Contract

```typescript
// Single event type with discriminated union
type ResearchEvent = 
  | { type: 'iteration'; data: { current: number; total: number } }
  | { type: 'thinking'; data: { content: string } }
  | { type: 'tool_call'; data: { tool: string; args: any } }
  | { type: 'tool_result'; data: { tool: string; result: any } }
  | { type: 'response'; data: { content: string; sources: string[] } }
  | { type: 'complete'; data: { stats: ResearchStats } }
  | { type: 'error'; data: { message: string } };
```

### 4. Clean Component Structure

```
src/
  hooks/
    useResearch.ts         # Main hook that encapsulates all research logic
    useWebSocket.ts        # Generic WebSocket hook
  
  services/
    researchService.ts     # API calls and WebSocket management
    eventProcessor.ts      # Processes events into state updates
  
  components/
    Chat/
      ChatContainer.tsx    # Smart component with hook
      ChatView.tsx        # Pure display component
      MessageList.tsx     # Pure message renderer
      MessageInput.tsx    # Pure input component
    
    Research/
      ResearchTrace.tsx   # Pure trace display
```

### 5. Usage Example

```typescript
function ChatContainer() {
  const { messages, sendMessage, state } = useResearch();
  
  return (
    <ChatView
      messages={messages}
      onSendMessage={sendMessage}
      isLoading={state.type === 'researching'}
    />
  );
}
```

## Benefits

1. **Predictable State**: No more juggling multiple state variables
2. **Type Safety**: Exhaustive TypeScript checks for all states/events
3. **Testability**: Pure components and isolated business logic
4. **Maintainability**: Clear separation of concerns
5. **Performance**: Reduced re-renders with proper memoization
6. **Debugging**: Single state object makes it easy to log/inspect

## Migration Strategy

1. Build new architecture in parallel (new components)
2. Test thoroughly with all edge cases
3. Switch over once stable
4. Remove old code

## Implementation Effort

- Estimated time: 4-6 hours for core functionality
- Additional 2-3 hours for testing and edge cases
- Can be done incrementally without breaking existing code