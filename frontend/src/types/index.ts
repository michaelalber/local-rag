export interface Book {
  id: string;
  title: string;
  author: string | null;
  file_type: string;
  chunk_count: number;
}

export interface Source {
  content: string;
  page_number: number | null;
  chapter: string | null;
  book_id: string;
  has_code: boolean;
  code_language: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  latency_ms: number | null;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  timestamp: Date;
  isStreaming?: boolean;
}

// Query source options for selecting between Books, Compliance, or Both
export type QuerySource = 'books' | 'compliance' | 'both';

// Health check response
export interface HealthResponse {
  status: string;
  version: string;
  aegis_available: boolean;
  aegis_transport: 'stdio' | 'http' | null;
}

// SSE event types for streaming
export interface StreamStartEvent {
  status: 'processing';
}

export interface StreamSourcesEvent {
  book_sources: Array<{
    content: string;
    page_number: number | null;
    chapter: string | null;
    book_id: string | null;
  }>;
  compliance_count: number;
}

export interface StreamTokenEvent {
  content: string;
}

export interface StreamDoneEvent {
  status: 'complete';
}

export interface StreamErrorEvent {
  message: string;
}
