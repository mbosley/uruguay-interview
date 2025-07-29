import React, { useState, useEffect } from 'react';
import { X, Calendar, MapPin, Tag, User, FileText, ChevronRight, Loader } from 'lucide-react';
import { Interview } from '../../types/research.types';
import { researchAPI } from '../../services/api';
import clsx from 'clsx';

interface InterviewViewerProps {
  interview: Interview;
  onClose: () => void;
}

export const InterviewViewer: React.FC<InterviewViewerProps> = ({ interview, onClose }) => {
  const [interviewData, setInterviewData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [selectedTurn, setSelectedTurn] = useState<number>(0);

  useEffect(() => {
    const fetchInterview = async () => {
      try {
        setLoading(true);
        setError(undefined);
        const data = await researchAPI.getInterview(interview.id);
        setInterviewData(data);
      } catch (err) {
        console.error('Failed to fetch interview:', err);
        setError('Failed to load interview content');
      } finally {
        setLoading(false);
      }
    };

    fetchInterview();
  }, [interview.id]);

  const renderTurn = (turn: any, index: number) => {
    const isInterviewer = turn.speaker === 'Interviewer';
    
    return (
      <div
        key={index}
        className={clsx(
          'p-4 rounded-lg transition-all duration-200 cursor-pointer',
          selectedTurn === index ? 'ring-2 ring-uruguay-blue' : '',
          isInterviewer ? 'bg-gray-800/50' : 'bg-uruguay-blue/10',
          'hover:bg-opacity-70'
        )}
        onClick={() => setSelectedTurn(index)}
      >
        <div className="flex items-center space-x-2 mb-2">
          <User className={clsx(
            'w-4 h-4',
            isInterviewer ? 'text-gray-400' : 'text-uruguay-blue'
          )} />
          <span className={clsx(
            'text-sm font-medium',
            isInterviewer ? 'text-gray-400' : 'text-uruguay-blue'
          )}>
            {turn.speaker}
          </span>
          <span className="text-xs text-gray-500">Turn {index + 1}</span>
        </div>
        <p className="text-sm text-gray-300 line-clamp-3">{turn.text}</p>
        
        {turn.annotations && turn.annotations.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {turn.annotations.slice(0, 3).map((annotation: any, idx: number) => (
              <span
                key={idx}
                className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded-full"
              >
                {annotation.theme || annotation.type}
              </span>
            ))}
            {turn.annotations.length > 3 && (
              <span className="text-xs text-gray-500">
                +{turn.annotations.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl w-full max-w-4xl h-[80vh] flex flex-col bg-gray-900/95 border border-white/20">
        {/* Header */}
        <div className="p-6 border-b border-white/10">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">{interview.title}</h2>
              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-4 h-4" />
                  <span>{interview.date}</span>
                </div>
                {interview.location && (
                  <div className="flex items-center space-x-1">
                    <MapPin className="w-4 h-4" />
                    <span>{interview.location}</span>
                  </div>
                )}
                <div className="flex items-center space-x-1">
                  <FileText className="w-4 h-4" />
                  <span>{interview.turns} turns</span>
                </div>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Themes */}
          {interview.themes.length > 0 && (
            <div className="mt-4 flex items-center space-x-2">
              <Tag className="w-4 h-4 text-gray-400" />
              <div className="flex flex-wrap gap-2">
                {interview.themes.map((theme, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 bg-uruguay-blue/20 text-uruguay-blue rounded-full text-sm"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Loader className="w-8 h-8 text-uruguay-blue animate-spin mx-auto mb-4" />
                <p className="text-gray-400">Loading interview content...</p>
              </div>
            </div>
          ) : error ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <p className="text-red-400 mb-4">{error}</p>
                <button
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
                >
                  Retry
                </button>
              </div>
            </div>
          ) : interviewData ? (
            <div className="h-full flex">
              {/* Turns list */}
              <div className="w-1/2 border-r border-white/10 overflow-y-auto p-4 space-y-3">
                <h3 className="text-sm font-medium text-gray-400 mb-3">Interview Transcript</h3>
                {interviewData.turns?.map((turn: any, idx: number) => renderTurn(turn, idx))}
              </div>

              {/* Interview Summary */}
              <div className="w-1/2 p-4 overflow-y-auto">
                <h3 className="text-sm font-medium text-gray-400 mb-3">Interview Analysis</h3>
                
                {/* AI Summary */}
                {interviewData.annotation && (
                  <div className="space-y-4">
                    {/* Summary Overview */}
                    {interviewData.annotation.summary?.overview && (
                      <div>
                        <h4 className="text-sm font-medium text-uruguay-blue mb-2">Summary</h4>
                        <div className="p-4 bg-uruguay-blue/10 rounded-lg border border-uruguay-blue/20">
                          <p className="text-sm text-gray-300">
                            {interviewData.annotation.summary.overview}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Key Themes */}
                    {((interviewData.annotation.key_themes && interviewData.annotation.key_themes.length > 0) ||
                      (interviewData.annotation.summary?.key_themes && interviewData.annotation.summary.key_themes.length > 0)) && (
                      <div>
                        <h4 className="text-sm font-medium text-purple-400 mb-2">Key Themes</h4>
                        <div className="space-y-2">
                          {(interviewData.annotation.key_themes || interviewData.annotation.summary?.key_themes || []).map((theme: any, idx: number) => (
                            <div
                              key={idx}
                              className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20"
                            >
                              <div className="flex items-start space-x-2">
                                <ChevronRight className="w-3 h-3 text-purple-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <span className="text-sm font-medium text-purple-400">
                                    {theme.theme}
                                  </span>
                                  {theme.description && (
                                    <p className="text-xs text-gray-400 mt-1">
                                      {theme.description}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Notable Quotes */}
                    {interviewData.annotation.notable_quotes && interviewData.annotation.notable_quotes.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-emerald-400 mb-2">Notable Quotes</h4>
                        <div className="space-y-2">
                          {interviewData.annotation.notable_quotes.slice(0, 3).map((quote: any, idx: number) => (
                            <div key={idx} className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                              <p className="text-xs text-gray-300 italic">"{quote.text || quote}"</p>
                              {quote.context && (
                                <p className="text-xs text-gray-500 mt-1">— {quote.context}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Issue Tags */}
                    {interviewData.annotation.issue_tags && interviewData.annotation.issue_tags.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-orange-400 mb-2">Issues Discussed</h4>
                        <div className="flex flex-wrap gap-2">
                          {interviewData.annotation.issue_tags.map((tag: string, idx: number) => (
                            <span
                              key={idx}
                              className="px-3 py-1 bg-orange-500/20 text-orange-300 rounded-full text-xs"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Metadata */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-400 mb-2">Interview Metadata</h4>
                      <div className="p-4 bg-gray-800/50 rounded-lg">
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Total Turns:</span>
                            <span className="text-gray-300">{interviewData.turns?.length || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Date:</span>
                            <span className="text-gray-300">{interview.date}</span>
                          </div>
                          {interview.location && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Location:</span>
                              <span className="text-gray-300">{interview.location}</span>
                            </div>
                          )}
                          {interviewData.metadata?.duration && (
                            <div className="flex justify-between">
                              <span className="text-gray-400">Duration:</span>
                              <span className="text-gray-300">{interviewData.metadata.duration}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {!interviewData.annotation && (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-gray-500 text-sm">No analysis available for this interview</p>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};