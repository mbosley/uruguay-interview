import React, { useState } from 'react';
import { Search, Sparkles, ChevronRight, Brain } from 'lucide-react';

interface QuestionInputProps {
  onSubmit: (question: string) => void;
  isLoading?: boolean;
  suggestions?: string[];
}

export const QuestionInput: React.FC<QuestionInputProps> = ({ 
  onSubmit, 
  isLoading = false,
  suggestions = [
    "What are the main healthcare concerns mentioned by citizens?",
    "How do citizens describe security issues in their communities?",
    "What infrastructure problems are most frequently mentioned?",
    "Compare rural vs urban perspectives on public services",
    "What do people say about education quality?"
  ]
}) => {
  const [question, setQuestion] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim() && !isLoading) {
      onSubmit(question.trim());
      setQuestion('');
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuestion(suggestion);
    onSubmit(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-4">
          Ask a Research Question
        </h2>
        <p className="text-gray-400">
          I'll analyze the 37 citizen consultation interviews to provide comprehensive insights
        </p>
      </div>

      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-uruguay-blue to-purple-600 rounded-xl blur-xl opacity-20"></div>
          <div className="relative flex items-center">
            <input
              type="text"
              value={question}
              onChange={(e) => {
                setQuestion(e.target.value);
                if (!e.target.value.trim()) setShowSuggestions(true);
              }}
              placeholder="Ask about healthcare, education, security, infrastructure..."
              className="flex-1 px-6 py-4 bg-white/5 border border-white/10 rounded-l-xl focus:outline-none focus:ring-2 focus:ring-uruguay-blue/50 focus:border-uruguay-blue/50 text-white placeholder-gray-500 transition-all duration-200 text-lg"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="px-6 py-4 bg-gradient-to-r from-uruguay-blue to-purple-600 text-white rounded-r-xl hover:shadow-lg hover:shadow-purple-500/25 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 flex items-center space-x-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Researching...</span>
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  <span>Start Research</span>
                  <ChevronRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {showSuggestions && suggestions.length > 0 && (
        <div className="animate-slideIn">
          <div className="flex items-center space-x-2 mb-4">
            <Sparkles className="w-5 h-5 text-uruguay-yellow" />
            <span className="text-sm font-medium text-gray-300">Example Questions</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={isLoading}
                className="glass rounded-lg p-4 text-left hover:bg-white/10 transition-all duration-200 group disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="flex items-start space-x-3">
                  <Brain className="w-5 h-5 text-uruguay-blue mt-0.5 group-hover:text-uruguay-yellow transition-colors" />
                  <span className="text-sm text-gray-300 group-hover:text-white transition-colors">
                    {suggestion}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mt-8 text-center text-xs text-gray-500">
        <p>The AI will show its reasoning process as it analyzes your query across all interviews</p>
      </div>
    </div>
  );
};