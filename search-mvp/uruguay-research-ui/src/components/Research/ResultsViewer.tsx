import React, { useEffect, useState } from 'react';
import { FileText, Quote, Star, Copy, Check } from 'lucide-react';

interface ResultsViewerProps {
  content: string;
  sources?: string[];
  isStreaming?: boolean;
  streamingDelay?: number;
}

export const ResultsViewer: React.FC<ResultsViewerProps> = ({ 
  content, 
  sources = [], 
  isStreaming = false,
  streamingDelay = 30
}) => {
  const [copied, setCopied] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  // When streaming is true, content is being built up chunk by chunk
  // When streaming is false, we have the complete content
  const displayedContent = content;

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatContent = (text: string) => {
    // Convert markdown-style formatting to HTML
    return text
      .split('\n')
      .map((line, idx) => {
        // Headers
        if (line.startsWith('### ')) {
          return <h3 key={idx} className="text-lg font-semibold text-white mt-6 mb-3">{line.substring(4)}</h3>;
        }
        if (line.startsWith('## ')) {
          return <h2 key={idx} className="text-xl font-bold text-white mt-6 mb-3">{line.substring(3)}</h2>;
        }
        if (line.startsWith('# ')) {
          return <h1 key={idx} className="text-2xl font-bold text-white mt-6 mb-3">{line.substring(2)}</h1>;
        }
        
        // Bold text
        const boldRegex = /\*\*(.*?)\*\*/g;
        const parts = line.split(boldRegex);
        const formattedLine = parts.map((part, i) => 
          i % 2 === 1 ? <strong key={i} className="font-semibold text-white">{part}</strong> : part
        );
        
        // Bullet points
        if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
          return (
            <li key={idx} className="ml-6 mb-2 text-gray-300">
              {formattedLine.slice(1)}
            </li>
          );
        }
        
        // Numbered lists
        const numberedMatch = line.match(/^(\d+)\.\s(.+)/);
        if (numberedMatch) {
          return (
            <li key={idx} className="ml-6 mb-2 text-gray-300 list-decimal">
              {formattedLine.slice(1)}
            </li>
          );
        }
        
        // Regular paragraphs
        if (line.trim()) {
          return <p key={idx} className="mb-4 text-gray-300 leading-relaxed">{formattedLine}</p>;
        }
        
        return null;
      })
      .filter(Boolean);
  };

  return (
    <div className="glass rounded-xl p-6 border border-white/10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-uruguay-blue" />
          <h3 className="text-lg font-semibold text-white">Research Findings</h3>
        </div>
        <button
          onClick={handleCopy}
          className="p-2 hover:bg-white/10 rounded-lg transition-all duration-200"
          title="Copy to clipboard"
        >
          {copied ? (
            <Check className="w-4 h-4 text-emerald-400" />
          ) : (
            <Copy className="w-4 h-4 text-gray-400" />
          )}
        </button>
      </div>
      
      <div className="prose prose-invert max-w-none">
        {formatContent(displayedContent)}
        {isStreaming && (
          <span className="inline-block w-1 h-5 bg-white animate-pulse ml-1"></span>
        )}
      </div>
      
      {sources.length > 0 && (
        <div className="mt-6 pt-6 border-t border-white/10">
          <div className="flex items-center space-x-2 mb-3">
            <Star className="w-4 h-4 text-uruguay-yellow" />
            <span className="text-sm font-medium text-gray-300">Referenced Sources</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {sources.map((source, idx) => (
              <div 
                key={idx}
                className="flex items-center space-x-2 px-3 py-1.5 bg-white/10 rounded-full hover:bg-white/20 transition-colors duration-200 cursor-pointer"
              >
                <Quote className="w-3 h-3 text-uruguay-blue" />
                <span className="text-xs text-gray-300">{source}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};