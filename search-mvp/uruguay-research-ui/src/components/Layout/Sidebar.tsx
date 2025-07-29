import React, { useState } from 'react';
import { Search, FileText, Calendar, MapPin, Hash, Layers } from 'lucide-react';
import { Interview } from '../../types/research.types';
import clsx from 'clsx';

interface SidebarProps {
  interviews: Interview[];
  selectedInterview?: Interview;
  onSelectInterview: (interview: Interview) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  interviews, 
  selectedInterview, 
  onSelectInterview 
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredInterviews = interviews.filter(interview =>
    interview.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    interview.themes.some(theme => theme.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="w-96 glass border-r border-white/10 flex flex-col">
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Interview Sources</h2>
          <div className="text-sm text-gray-400">
            {filteredInterviews.length} of {interviews.length}
          </div>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search interviews..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-3 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-uruguay-blue/50 focus:border-uruguay-blue/50 text-white placeholder-gray-500 transition-all duration-200"
          />
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {filteredInterviews.map(interview => (
          <div
            key={interview.id}
            onClick={() => onSelectInterview(interview)}
            className={clsx(
              'p-4 border-b border-white/5 cursor-pointer transition-all duration-200',
              selectedInterview?.id === interview.id 
                ? 'bg-gradient-to-r from-uruguay-blue/20 to-purple-600/20 border-l-2 border-uruguay-blue' 
                : 'hover:bg-white/5'
            )}
          >
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-white/10 rounded-lg">
                <FileText className="w-4 h-4 text-gray-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-white text-sm">{interview.title}</h3>
                <div className="flex items-center space-x-3 mt-1 text-xs text-gray-500">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>{interview.date}</span>
                  </span>
                  {interview.location && (
                    <>
                      <span>•</span>
                      <span className="flex items-center space-x-1">
                        <MapPin className="w-3 h-3" />
                        <span>{interview.location}</span>
                      </span>
                    </>
                  )}
                  <span>•</span>
                  <span className="flex items-center space-x-1">
                    <Hash className="w-3 h-3" />
                    <span>{interview.turns} turns</span>
                  </span>
                </div>
                {interview.themes.length > 0 && (
                  <div className="mt-2 flex items-start space-x-1">
                    <Layers className="w-3 h-3 text-gray-500 mt-0.5 flex-shrink-0" />
                    <div className="flex flex-wrap gap-1">
                      {interview.themes.map((theme, idx) => (
                        <span key={idx} className="text-[10px] px-1.5 py-0.5 bg-white/10 rounded text-gray-300">
                          {theme}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};