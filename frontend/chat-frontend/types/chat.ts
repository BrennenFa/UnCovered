export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  citations?: Record<string, string>; // Map of citation keys to S3 URLs
  timestamp: Date;
  isStreaming?: boolean;
}

export interface Source {
  document_id: string;
  page: string;
  source: string;
  url: string;
}

export interface ChatResponse {
  answer: string;
  citations?: Record<string, string>; // Map of citation keys to S3 URLs
  sources?: Source[];
}
