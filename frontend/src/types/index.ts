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

// Query source options
export type QuerySource = 'books' | 'compliance' | 'mslearn' | 'export_control' | 'all' | 'both';

// MCP source status from health check
export interface MCPSource {
  name: string;
  display_name: string;
  available: boolean;
}

// Health check response
export interface HealthResponse {
  status: string;
  version: string;
  mcp_sources: MCPSource[];
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
