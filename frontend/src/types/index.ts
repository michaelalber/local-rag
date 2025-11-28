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
}
