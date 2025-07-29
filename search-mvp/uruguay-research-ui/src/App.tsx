import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Layout/Header';
import { Sidebar } from './components/Layout/Sidebar';
import { ChatInterface } from './components/Chat/ChatInterface';
import { InterviewViewer } from './components/Research/InterviewViewer';
import { ResearchWebSocket } from './services/websocket';
import { researchAPI } from './services/api';
import { Interview, ResearchTrace, ReasoningStep, WebSocketMessage, ChatMessage } from './types/research.types';
// @ts-ignore - types are installed but TS might need restart
import { v4 as uuidv4 } from 'uuid';
import './services/unifiedLogger'; // Initialize unified logging
import { TestChat } from './TestChat';
import { SimpleFormTest } from './SimpleFormTest';
import { SimpleChatbot } from './SimpleChatbot';
import { SimpleChatbotWithTrace } from './SimpleChatbotWithTrace';
import { SimpleChatbotEager } from './SimpleChatbotEager';
import { MinimalTrace } from './MinimalTrace';
import { PreconnectTest } from './PreconnectTest';
import { AsyncWebSocketTest } from './AsyncWebSocketTest';
import { WebSocketDebugTest } from './WebSocketDebugTest';

function App() {
  const [interviews, setInterviews] = useState<Interview[]>([]);
  const [selectedInterview, setSelectedInterview] = useState<Interview | undefined>(undefined);
  const [showInterviewViewer, setShowInterviewViewer] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isResearching, setIsResearching] = useState(false);
  const [currentTrace, setCurrentTrace] = useState<ResearchTrace[]>([]);
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState<ChatMessage | null>(null);
  const [currentJobId, setCurrentJobId] = useState<string>();
  const [error, setError] = useState<string>();
  const [currentIteration, setCurrentIteration] = useState<number>(0);
  const [testMode, setTestMode] = useState<boolean>(true); // Default to test mode for debugging
  
  // Use ref to avoid closure issues with trace
  const currentTraceRef = useRef<ResearchTrace[]>([]);

  // Load interviews on mount
  useEffect(() => {
    const loadInterviews = async () => {
      try {
        const data = await researchAPI.getInterviews();
        setInterviews(data);
      } catch (err) {
        console.error('Failed to load interviews:', err);
        // Use mock data as fallback for development
        const mockInterviews: Interview[] = Array.from({ length: 37 }, (_, i) => ({
          id: `${(i + 1).toString().padStart(3, '0')}`,
          title: `Interview ${(i + 1).toString().padStart(3, '0')}`,
          date: '2025-05-28',
          location: i % 3 === 0 ? 'Montevideo' : i % 3 === 1 ? 'Salto' : 'Rivera',
          themes: ['healthcare', 'education', 'security'].slice(0, Math.floor(Math.random() * 3) + 1),
          turns: Math.floor(Math.random() * 50) + 100
        }));
        setInterviews(mockInterviews);
      }
    };
    loadInterviews();
  }, []);

  // Handle interview selection
  const handleSelectInterview = (interview: Interview) => {
    setSelectedInterview(interview);
    setShowInterviewViewer(true);
  };

  const handleSendMessage = async (question: string) => {
    console.log('🎯 handleSendMessage called with:', question);
    
    // Add user message
    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: question,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Create assistant message placeholder
    const assistantMessage: ChatMessage = {
      id: uuidv4(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
      trace: []
    };
    console.log('🤖 Creating assistant message:', assistantMessage);
    setMessages(prev => [...prev, assistantMessage]);
    setCurrentAssistantMessage(assistantMessage);

    try {
      setIsResearching(true);
      setError(undefined);
      setCurrentTrace([]); // Clear trace when starting new research
      currentTraceRef.current = []; // Clear ref too
      setCurrentIteration(0);

      // Start research job
      console.log('🚀 Starting research for:', question, 'Test mode:', testMode);
      const apiStartTime = Date.now();
      const { job_id } = await researchAPI.startResearch(question, 'moonshot', testMode);
      const apiEndTime = Date.now();
      console.log(`📋 Got job ID: ${job_id} (API took ${apiEndTime - apiStartTime}ms)`);
      setCurrentJobId(job_id);

      // Connect WebSocket for real-time updates
      const wsStartTime = Date.now();
      console.log('🔌 Creating WebSocket for job:', job_id);
      const ws = new ResearchWebSocket(job_id);
      console.log(`🔨 WebSocket instance created (took ${Date.now() - wsStartTime}ms)`);
      
      // Store WebSocket instance for debugging
      (window as any).debugWs = ws;
      
      console.log('🔗 Calling ws.connect()...');
      const connectStartTime = Date.now();
      ws.connect({
        onConnect: () => {
          console.log(`🎉 WebSocket onConnect fired (connect took ${Date.now() - connectStartTime}ms)`);
        },
        onMessage: (message: WebSocketMessage) => {
          console.log('📨 WebSocket Event:', {
            type: message.type,
            iteration: message.iteration,
            data: message.data,
            timestamp: new Date().toISOString()
          });
          
          switch (message.type) {
            case 'iteration_start':
              // Update current iteration
              setCurrentIteration(message.data.current);
              console.log('🔄 Setting current iteration:', message.data.current);
              
              // Only create trace if it doesn't exist
              setCurrentTrace(prev => {
                const exists = prev.some(t => t.iteration === message.data.current);
                console.log('🔍 Checking if iteration exists:', { 
                  iteration: message.data.current, 
                  exists, 
                  currentTraces: prev.map(t => t.iteration) 
                });
                
                if (!exists) {
                  const newTrace = {
                    iteration: message.data.current,
                    steps: [],
                    timestamp: new Date()
                  };
                  console.log('➕ Creating new trace for iteration:', newTrace);
                  const updated = [...prev, newTrace];
                  currentTraceRef.current = updated; // Update ref
                  return updated;
                }
                return prev;
              });
              break;
              
            case 'thinking':
              // Add thinking step
              if (message.data.content) {
                const thinkingStep: ReasoningStep = {
                  type: 'thinking',
                  content: message.data.content,
                  status: 'complete'
                };
                console.log('💭 Adding thinking step:', {
                  step: thinkingStep,
                  iteration: message.iteration || currentIteration
                });
                updateCurrentTrace(thinkingStep, message.iteration || currentIteration);
              }
              break;
              
            case 'tool_call':
              // Format tool call nicely
              const args = message.data.args || {};
              const formattedArgs = Object.entries(args)
                .map(([key, value]) => `${key}: "${value}"`)
                .join(', ');
              
              const toolStep: ReasoningStep = {
                type: 'tool',
                content: `${message.data.tool}(${formattedArgs})`,
                tool: message.data.tool,
                status: 'active'
              };
              console.log('🔧 Adding tool call:', {
                step: toolStep,
                iteration: message.iteration || currentIteration
              });
              updateCurrentTrace(toolStep, message.iteration || currentIteration);
              break;
              
            case 'tool_result':
              // Update the last tool step with results
              console.log('✅ Tool result received:', {
                tool: message.data.tool,
                preview: message.data.metadata?.preview,
                iteration: message.iteration || currentIteration
              });
              
              setCurrentTrace(prev => {
                const newTraces = [...prev];
                const iteration = message.iteration || currentIteration;
                const trace = newTraces.find(t => t.iteration === iteration);
                
                console.log('🔍 Looking for trace:', { iteration, found: !!trace });
                
                if (trace) {
                  // Find the last tool step that's active
                  const toolStepIndex = trace.steps.findIndex(
                    (s, idx) => s.type === 'tool' && s.status === 'active' &&
                    !trace.steps.slice(idx + 1).some(step => step.type === 'tool' && step.status === 'active')
                  );
                  
                  console.log('🔍 Found tool step to update:', { 
                    index: toolStepIndex, 
                    step: toolStepIndex >= 0 ? trace.steps[toolStepIndex] : null 
                  });
                  
                  if (toolStepIndex >= 0) {
                    trace.steps[toolStepIndex] = {
                      ...trace.steps[toolStepIndex],
                      status: 'complete',
                      results: message.data.metadata?.preview || 'Completed'
                    };
                    console.log('✏️ Updated tool step:', trace.steps[toolStepIndex]);
                  }
                }
                currentTraceRef.current = newTraces; // Update ref
                return newTraces;
              });
              break;
              
            case 'analysis':
              const analysisStep: ReasoningStep = {
                type: 'analysis',
                content: message.data.message || 'Analyzing findings...',
                status: 'complete'
              };
              updateCurrentTrace(analysisStep, message.iteration || currentIteration);
              break;
              
            case 'progress':
              // Could show in a toast or status bar
              console.log('Progress:', message.data.message);
              break;
              
            case 'response_start':
              // Just mark that we're about to receive the response
              break;
              
            case 'response_end':
              // Set the complete response at once
              console.log('🏁 Response end received:', {
                data: message.data,
                hasResponse: !!message.data?.response,
                responseLength: message.data?.response?.length,
                traceLength: currentTraceRef.current.length,
                hasAssistantMessage: !!currentAssistantMessage,
                assistantMessageId: currentAssistantMessage?.id
              });
              
              if (currentAssistantMessage) {
                console.log('📝 Processing response_end - currentAssistantMessage:', {
                  id: currentAssistantMessage.id,
                  currentContent: currentAssistantMessage.content,
                  currentIsStreaming: currentAssistantMessage.isStreaming
                });
                
                setMessages(prev => {
                  console.log('📝 Current messages before update:', prev.map(m => ({
                    id: m.id,
                    role: m.role,
                    content: m.content?.substring(0, 50),
                    isStreaming: m.isStreaming
                  })));
                  
                  const updated = prev.map(msg => {
                    if (msg.id === currentAssistantMessage.id) {
                      const updatedMsg = { 
                        ...msg, 
                        content: message.data.response || '',
                        sources: message.data.sources || [],
                        isStreaming: false,
                        trace: currentTraceRef.current // Use ref to get latest trace
                      };
                      console.log('📝 Updated message with response:', {
                        messageId: updatedMsg.id,
                        hasContent: !!updatedMsg.content,
                        contentLength: updatedMsg.content?.length,
                        contentPreview: updatedMsg.content?.substring(0, 100),
                        isStreaming: updatedMsg.isStreaming,
                        traceLength: updatedMsg.trace?.length
                      });
                      return updatedMsg;
                    }
                    return msg;
                  });
                  
                  console.log('📝 Messages after update:', updated.map(m => ({
                    id: m.id,
                    role: m.role,
                    content: m.content?.substring(0, 50),
                    isStreaming: m.isStreaming
                  })));
                  
                  return updated;
                });
              } else {
                console.warn('⚠️ No currentAssistantMessage when response_end received!');
              }
              setIsResearching(false);
              setCurrentAssistantMessage(null);
              // Keep WebSocket open briefly for any final events (like stats)
              setTimeout(() => {
                console.log('🔌 Closing WebSocket after response_end');
                ws.disconnect();
              }, 500);
              break;
              
            case 'stats':
              // Add stats to the assistant message
              if (currentAssistantMessage) {
                setMessages(prev => prev.map(msg => 
                  msg.id === currentAssistantMessage.id 
                    ? { ...msg, stats: message.data }
                    : msg
                ));
              }
              break;
              
            case 'error':
              setError(message.data.error);
              setIsResearching(false);
              ws.disconnect();
              break;
              
            // Legacy support - ignore if we already got response_end
            case 'result':
              console.log('📊 Legacy result event received (ignoring, we use response_end now)');
              // Don't process - we handle everything in response_end
              break;
          }
        },
        onError: (error) => {
          console.error('WebSocket error:', error);
          setError('Connection error. Please try again.');
          setIsResearching(false);
        },
        onDisconnect: () => {
          console.log('WebSocket disconnected');
        }
      });

    } catch (err) {
      console.error('❌ Research error:', err);
      setError('Failed to start research. Please try again.');
      setIsResearching(false);
      // Also clear the assistant message on error
      if (currentAssistantMessage) {
        setMessages(prev => prev.filter(msg => msg.id !== currentAssistantMessage.id));
      }
    }
  };

  const updateCurrentTrace = (step: ReasoningStep, iteration?: number) => {
    console.log('📊 updateCurrentTrace called:', { step, iteration, currentIteration });
    
    setCurrentTrace(prev => {
      const targetIteration = iteration || currentIteration || 1;
      console.log('🎯 Target iteration:', targetIteration, 'Previous traces:', prev.length);
      
      if (prev.length === 0) {
        const newTrace = [{
          iteration: targetIteration,
          steps: [step],
          timestamp: new Date()
        }];
        console.log('📝 Creating first trace:', newTrace);
        currentTraceRef.current = newTrace; // Update ref
        return newTrace;
      }
      
      const newTraces = [...prev];
      let trace = newTraces.find(t => t.iteration === targetIteration);
      console.log('🔍 Found existing trace:', !!trace);
      
      if (!trace) {
        // Create new trace if it doesn't exist
        trace = {
          iteration: targetIteration,
          steps: [],
          timestamp: new Date()
        };
        newTraces.push(trace);
        console.log('➕ Created new trace for iteration:', targetIteration);
      }
      
      // Check if this step already exists (to prevent duplicates)
      const isDuplicate = trace.steps.some(s => 
        s.type === step.type && 
        s.content === step.content &&
        s.tool === step.tool
      );
      
      if (!isDuplicate) {
        trace.steps.push(step);
        console.log('✅ Added step to trace:', { 
          iteration: targetIteration, 
          stepType: step.type, 
          totalSteps: trace.steps.length 
        });
      } else {
        console.log('⚠️ Skipped duplicate step');
      }
      
      console.log('📊 Current trace state:', {
        iterations: newTraces.map(t => ({ 
          iteration: t.iteration, 
          steps: t.steps.length 
        }))
      });
      
      currentTraceRef.current = newTraces; // Update ref
      return newTraces;
    });
  };

  const handleExport = async () => {
    if (!currentJobId) return;
    
    try {
      const blob = await researchAPI.exportResults(currentJobId, 'pdf');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `research-results-${currentJobId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Export error:', err);
      setError('Failed to export results');
    }
  };

  // For debugging: show test components
  const showDebugComponents = false;
  
  if (showDebugComponents) {
    return <WebSocketDebugTest />;
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <Header onExport={handleExport} />
      
      {/* Test mode toggle */}
      <div className="absolute top-4 right-48 z-50">
        <label className="flex items-center space-x-2 text-white text-sm">
          <input
            type="checkbox"
            checked={testMode}
            onChange={(e) => setTestMode(e.target.checked)}
            className="rounded"
          />
          <span>Test Mode (2 iterations)</span>
        </label>
      </div>
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar 
          interviews={interviews}
          selectedInterview={selectedInterview}
          onSelectInterview={handleSelectInterview}
        />
        
        <main className="flex-1 overflow-hidden flex flex-col">
          {(() => {
            console.log('🎭 ChatInterface props:', {
              isResearching,
              currentTraceLength: currentTrace.length,
              currentTrace: isResearching ? currentTrace : undefined,
              messagesCount: messages.length,
              onSendMessage: typeof handleSendMessage,
              handleSendMessageDefined: !!handleSendMessage
            });
            return null;
          })()}
          <ChatInterface
            messages={messages}
            isLoading={isResearching}
            onSendMessage={handleSendMessage}
            currentTrace={currentTrace}
            isResearching={isResearching}
          />
          
          {error && (
            <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-200 max-w-md">
              {error}
            </div>
          )}
        </main>
      </div>

      {/* Interview Viewer Modal */}
      {showInterviewViewer && selectedInterview && (
        <InterviewViewer
          interview={selectedInterview}
          onClose={() => setShowInterviewViewer(false)}
        />
      )}
    </div>
  );
}

export default App;