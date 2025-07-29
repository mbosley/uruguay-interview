export interface Interview {
  id: string;
  title: string;
  date: string;
  location?: string;
  themes: string[];
  turns: number;
}

export interface ResearchTool {
  name: string;
  description: string;
  icon: string;
}

export interface ToolCall {
  id: string;
  tool: string;
  args: Record<string, any>;
  status: 'pending' | 'active' | 'complete';
  result?: string;
  duration?: number;
  timestamp: Date;
}

export interface ReasoningStep {
  type: 'thinking' | 'tool' | 'analysis';
  content: string;
  tool?: string;
  results?: string;
  status: 'pending' | 'active' | 'complete';
  duration?: number;
}

export interface ResearchTrace {
  iteration: number;
  steps: ReasoningStep[];
  timestamp: Date;
}

export interface ResearchResult {
  question: string;
  traces: ResearchTrace[];
  finalResponse: string;
  stats: {
    duration: number;
    toolCalls: number;
    llmCalls: number;
    totalCost: number;
    inputTokens?: number;
    outputTokens?: number;
  };
  sources: string[];
}

export interface WebSocketMessage {
  type: 'iteration_start' | 'thinking' | 'reflection' | 'planning' | 
        'tool_call' | 'tool_result' | 'analysis' | 'progress' |
        'response_start' | 'response_chunk' | 'response_end' | 
        'error' | 'stats' | 'trace' | 'result';
  data: any;
  timestamp?: string;
  iteration?: number;
}

export const RESEARCH_TOOLS = {
  get_corpus_stats: {
    name: 'Corpus Overview',
    icon: 'FileText',
    description: 'Get overview statistics of the interview corpus'
  },
  search_interviews: {
    name: 'Search Interviews',
    icon: 'Search',
    description: 'Search for keywords across all interviews'
  },
  list_interview_themes: {
    name: 'List Themes',
    icon: 'Brain',
    description: 'Get all themes with occurrence counts'
  },
  get_interview_turn: {
    name: 'Get Interview',
    icon: 'MessageSquare',
    description: 'Retrieve specific interview content'
  },
  search_themes: {
    name: 'Search Themes',
    icon: 'Layers',
    description: 'Search for themes by keyword'
  },
  analyze_themes: {
    name: 'Analyze Themes',
    icon: 'GitBranch',
    description: 'Deep analysis of theme patterns'
  },
  scratchpad_append: {
    name: 'Research Notes',
    icon: 'BookOpen',
    description: 'Add to research journal'
  }
} as const;

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: string[];
  trace?: ResearchTrace[];
  isStreaming?: boolean;
  stats?: any;
}