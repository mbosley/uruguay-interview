import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const researchAPI = {
  // Start a new research job
  startResearch: async (question: string, provider: string = 'moonshot', testMode: boolean = false) => {
    const response = await apiClient.post('/research', {
      question,
      provider,
      max_iterations: testMode ? 2 : 8,
      test_mode: testMode,
    });
    return response.data;
  },

  // Get research job status
  getJobStatus: async (jobId: string) => {
    const response = await apiClient.get(`/research/${jobId}`);
    return response.data;
  },

  // Get list of interviews
  getInterviews: async () => {
    const response = await apiClient.get('/interviews');
    return response.data;
  },

  // Get interview content
  getInterview: async (interviewId: string) => {
    const response = await apiClient.get(`/interviews/${interviewId}`);
    return response.data;
  },

  // Export research results
  exportResults: async (jobId: string, format: 'pdf' | 'markdown' = 'markdown') => {
    const response = await apiClient.get(`/research/${jobId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },
};

export default apiClient;