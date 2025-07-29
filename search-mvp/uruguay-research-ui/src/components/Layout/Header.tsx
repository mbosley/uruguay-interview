import React from 'react';
import { Brain, Download, Share2 } from 'lucide-react';

interface HeaderProps {
  onExport?: () => void;
  onShare?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onExport, onShare }) => {
  return (
    <header className="glass border-b border-white/10">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-uruguay-blue to-purple-600 rounded-lg blur-lg opacity-50"></div>
                <div className="relative bg-gradient-to-r from-uruguay-blue to-purple-600 p-2 rounded-lg">
                  <Brain className="w-6 h-6 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white flex items-center space-x-2">
                  <span>Uruguay Interview Research</span>
                  <span className="text-uruguay-yellow">🇺🇾</span>
                </h1>
                <p className="text-xs text-gray-400">AI-Powered Qualitative Analysis</p>
              </div>
            </div>
            <div className="hidden lg:flex items-center space-x-2 ml-8">
              <div className="px-3 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30">
                <span className="text-xs text-emerald-400 font-medium">37 Interviews • 5,510 Turns • 121 Themes</span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button 
              onClick={onShare}
              className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-all duration-200 hover:bg-white/5 rounded-lg flex items-center space-x-2"
            >
              <Share2 className="w-4 h-4" />
              <span>Share</span>
            </button>
            <button 
              onClick={onExport}
              className="px-4 py-2 text-sm bg-gradient-to-r from-uruguay-blue to-purple-600 text-white rounded-lg hover:shadow-lg hover:shadow-purple-500/25 transition-all duration-200 transform hover:scale-105 flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export Report</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};