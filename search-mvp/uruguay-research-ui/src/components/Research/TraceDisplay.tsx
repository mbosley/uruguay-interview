import React, { useEffect, useRef } from 'react';
import { Brain, Search, FileText, GitBranch, Database, Layers, BookOpen, CheckCircle, Loader, ArrowUpRight, Zap } from 'lucide-react';
import { ResearchTrace, ReasoningStep } from '../../types/research.types';
import clsx from 'clsx';

interface TraceDisplayProps {
  traces: ResearchTrace[];
  isActive: boolean;
}

const getToolIcon = (toolName?: string) => {
  const iconMap: Record<string, React.ReactNode> = {
    'get_corpus_stats': <Database className="w-3.5 h-3.5 text-purple-400" />,
    'search_interviews': <Search className="w-3.5 h-3.5 text-purple-400" />,
    'list_interview_themes': <Layers className="w-3.5 h-3.5 text-purple-400" />,
    'get_interview_turn': <FileText className="w-3.5 h-3.5 text-purple-400" />,
    'get_interview_summary': <FileText className="w-3.5 h-3.5 text-purple-400" />,
    'search_themes': <GitBranch className="w-3.5 h-3.5 text-purple-400" />,
    'scratchpad_append': <BookOpen className="w-3.5 h-3.5 text-purple-400" />,
    'scratchpad_read': <BookOpen className="w-3.5 h-3.5 text-purple-400" />,
  };
  return iconMap[toolName || ''] || <Database className="w-3.5 h-3.5 text-purple-400" />;
};

const ReasoningStepComponent: React.FC<{ step: ReasoningStep; isLast: boolean }> = ({ step, isLast }) => {
  return (
    <div className={clsx(
      'transition-all duration-500',
      step.status === 'active' && 'scale-105 ml-2'
    )}>
      <div className={clsx(
        'flex items-start space-x-3',
        step.status === 'complete' && 'opacity-60'
      )}>
        <div className={clsx(
          'mt-0.5',
          step.status === 'active' && 'animate-pulse'
        )}>
          {step.type === 'thinking' && (
            <div className="w-7 h-7 bg-blue-500/20 rounded-lg flex items-center justify-center border border-blue-500/30">
              <Brain className="w-3.5 h-3.5 text-blue-400" />
            </div>
          )}
          {step.type === 'tool' && (
            <div className="w-7 h-7 bg-purple-500/20 rounded-lg flex items-center justify-center border border-purple-500/30">
              {getToolIcon(step.tool)}
            </div>
          )}
          {step.type === 'analysis' && (
            <div className="w-7 h-7 bg-emerald-500/20 rounded-lg flex items-center justify-center border border-emerald-500/30">
              <Zap className="w-3.5 h-3.5 text-emerald-400" />
            </div>
          )}
        </div>
        
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            {step.type === 'tool' && step.tool && (
              <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
                {step.tool.replace(/_/g, ' ')}
              </span>
            )}
            {step.type === 'thinking' && (
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">
                Thinking
              </span>
            )}
            {step.type === 'analysis' && (
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                Analysis
              </span>
            )}
            {step.status === 'complete' && (
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            )}
            {step.status === 'active' && (
              <Loader className="w-3.5 h-3.5 text-purple-400 animate-spin" />
            )}
          </div>
          
          <p className="text-xs text-gray-300 mt-1">{step.content}</p>
          
          {step.results && step.status === 'complete' && (
            <div className="mt-2 text-xs text-emerald-400 font-medium flex items-center space-x-1">
              <ArrowUpRight className="w-3 h-3" />
              <span>{step.results}</span>
            </div>
          )}
        </div>
      </div>
      
      {!isLast && (
        <div className="ml-3.5 mt-2 mb-2 w-px h-4 bg-gradient-to-b from-purple-500/30 to-transparent"></div>
      )}
    </div>
  );
};

export const TraceDisplay: React.FC<TraceDisplayProps> = ({ traces, isActive }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new traces are added
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [traces]);

  // Combine all steps into a single reasoning display
  const allSteps = traces.flatMap((trace) => 
    trace.steps.map(step => ({ ...step, iteration: trace.iteration }))
  );
  
  console.log('🖼️ TraceDisplay rendering:', {
    isActive,
    tracesCount: traces.length,
    totalSteps: allSteps.length,
    traces: traces.map(t => ({ 
      iteration: t.iteration, 
      steps: t.steps.map(s => ({ type: s.type, status: s.status })) 
    }))
  });

  return (
    <div className="glass rounded-2xl p-5 border border-purple-500/20 h-[300px] overflow-hidden relative">
      <div className="shimmer absolute inset-0 pointer-events-none"></div>
      
      <div className="flex items-center space-x-2 mb-4">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full blur-md opacity-50 animate-pulse"></div>
          <div className="relative p-2 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full">
            <Zap className="w-4 h-4 text-white" />
          </div>
        </div>
        <span className="text-sm font-medium text-purple-300">AI Reasoning Process</span>
        <div className="flex-1"></div>
        {isActive && (
          <div className="flex space-x-1">
            <div className="w-1 h-1 bg-purple-400 rounded-full animate-pulse"></div>
            <div className="w-1 h-1 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
            <div className="w-1 h-1 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
          </div>
        )}
      </div>
      
      <div className="space-y-3 overflow-y-auto h-[calc(100%-3rem)]">
        {allSteps.map((step, stepIdx) => (
          <ReasoningStepComponent 
            key={`${step.iteration}-${stepIdx}`} 
            step={step} 
            isLast={stepIdx === allSteps.length - 1}
          />
        ))}
        
        {isActive && allSteps.length === 0 && (
          <div className="flex items-center space-x-2 text-gray-400">
            <Loader className="w-4 h-4 animate-spin" />
            <span className="text-sm">AI is thinking...</span>
          </div>
        )}
        
        <div ref={bottomRef} />
      </div>
    </div>
  );
};