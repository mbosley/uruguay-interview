import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader, User, Bot, Zap, FileText } from 'lucide-react';
import { ChatMessage, ResearchTrace } from '../../types/research.types';
import { TraceDisplay } from '../Research/TraceDisplay';
import clsx from 'clsx';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  currentTrace?: ResearchTrace[];
  isResearching?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isLoading,
  onSendMessage,
  currentTrace,
  isResearching
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('🚀 handleSubmit called:', { inputValue, isLoading });
    if (inputValue.trim() && !isLoading) {
      console.log('📤 Calling onSendMessage with:', inputValue.trim());
      onSendMessage(inputValue.trim());
      setInputValue('');
    } else {
      console.log('⚠️ Not sending:', { hasInput: !!inputValue.trim(), isLoading });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto pb-6">
        <div className="max-w-4xl mx-auto space-y-6 p-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={clsx(
                'flex items-start space-x-3',
                message.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-gradient-to-br from-uruguay-blue to-purple-600 rounded-xl flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                </div>
              )}
              
              <div className={clsx(
                'flex flex-col max-w-[80%]',
                message.role === 'user' ? 'items-end' : 'items-start'
              )}>
                <div className={clsx(
                  'rounded-2xl px-5 py-3',
                  message.role === 'user' 
                    ? 'bg-uruguay-blue text-white' 
                    : 'glass border border-white/10'
                )}>
                  {message.role === 'user' ? (
                    <p className="text-sm">{message.content}</p>
                  ) : (
                    <>
                      {message.trace && message.trace.length > 0 && (
                        <div className="mb-4 -mx-2">
                          {(() => {
                            console.log('🎨 Rendering message trace:', { 
                              messageId: message.id, 
                              traceLength: message.trace.length,
                              trace: message.trace 
                            });
                            return null;
                          })()}
                          <TraceDisplay traces={message.trace} isActive={false} />
                        </div>
                      )}
                      
                      {(() => {
                        console.log('🎨 Rendering message content:', {
                          messageId: message.id,
                          isStreaming: message.isStreaming,
                          hasContent: !!message.content,
                          contentLength: message.content?.length,
                          contentPreview: message.content?.substring(0, 50),
                          showingLoader: message.isStreaming && !message.content
                        });
                        return null;
                      })()}
                      {message.isStreaming && !message.content ? (
                        <div className="flex items-center space-x-2">
                          <Loader className="w-4 h-4 text-uruguay-blue animate-spin" />
                          <span className="text-sm text-gray-400">Analyzing interviews...</span>
                        </div>
                      ) : (
                        <div className="prose prose-invert prose-sm max-w-none">
                          <p className="text-sm text-gray-300 whitespace-pre-wrap">{message.content}</p>
                        </div>
                      )}
                      
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-white/10">
                          <div className="flex items-center space-x-2 mb-2">
                            <FileText className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-400">Sources</span>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {message.sources.map((source, idx) => (
                              <span
                                key={idx}
                                className="text-xs px-2 py-1 bg-uruguay-blue/20 text-uruguay-blue rounded-full"
                              >
                                {source}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {message.stats && (
                        <div className="mt-3 pt-3 border-t border-white/10">
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="text-gray-400">Duration: <span className="text-gray-300">{message.stats.duration?.toFixed(1)}s</span></div>
                            <div className="text-gray-400">Tool calls: <span className="text-gray-300">{message.stats.toolCalls || 0}</span></div>
                            <div className="text-gray-400">Cost: <span className="text-gray-300">${message.stats.totalCost?.toFixed(4) || '0.00'}</span></div>
                            <div className="text-gray-400">Tokens: <span className="text-gray-300">{message.stats.inputTokens + message.stats.outputTokens || 0}</span></div>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
                
                <div className="mt-1 text-xs text-gray-500">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
              
              {message.role === 'user' && (
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-gray-700 rounded-xl flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {/* Current Research Progress */}
          {isResearching && currentTrace && currentTrace.length > 0 && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-gradient-to-br from-uruguay-blue to-purple-600 rounded-xl flex items-center justify-center animate-pulse">
                  <Zap className="w-5 h-5 text-white" />
                </div>
              </div>
              <div className="flex-1">
                {(() => {
                  console.log('🎨 Rendering live trace:', currentTrace);
                  return null;
                })()}
                <TraceDisplay traces={currentTrace} isActive={true} />
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-white/10 glass">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto p-4">
          <div className="relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the interviews..."
              disabled={isLoading}
              rows={1}
              className="w-full px-4 py-3 pr-12 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-uruguay-blue/50 focus:border-uruguay-blue/50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                minHeight: '48px',
                maxHeight: '120px'
              }}
            />
            <button
              type="submit"
              disabled={isLoading || !inputValue.trim()}
              className={clsx(
                'absolute right-2 bottom-2 p-2 rounded-lg transition-all duration-200',
                isLoading || !inputValue.trim()
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-uruguay-blue to-purple-600 text-white hover:shadow-lg hover:shadow-purple-500/25'
              )}
            >
              {isLoading ? (
                <Loader className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
          
          <div className="mt-2 flex items-center justify-between">
            <p className="text-xs text-gray-500">
              Press Enter to send, Shift+Enter for new line
            </p>
            {isLoading && (
              <p className="text-xs text-uruguay-blue flex items-center space-x-1">
                <Loader className="w-3 h-3 animate-spin" />
                <span>AI is researching...</span>
              </p>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};