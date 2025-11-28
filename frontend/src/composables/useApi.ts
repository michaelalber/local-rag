import { ref } from 'vue';
import type { Book, ChatResponse } from '../types';

// Generate session ID once per browser session
const SESSION_ID = sessionStorage.getItem('sessionId') || crypto.randomUUID();
sessionStorage.setItem('sessionId', SESSION_ID);

const API_BASE = '/api';

export function useApi() {
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function uploadBooks(files: File[]): Promise<Book[]> {
    loading.value = true;
    error.value = null;

    try {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));

      const response = await fetch(`${API_BASE}/books`, {
        method: 'POST',
        headers: {
          'session-id': SESSION_ID,
        },
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || `Upload failed: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Upload failed';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function getBooks(): Promise<Book[]> {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/books`, {
        headers: {
          'session-id': SESSION_ID,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch books: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch books';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function deleteBook(bookId: string): Promise<void> {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/books/${bookId}`, {
        method: 'DELETE',
        headers: {
          'session-id': SESSION_ID,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || `Delete failed: ${response.status}`);
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Delete failed';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function chat(query: string, topK: number = 5): Promise<ChatResponse> {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'session-id': SESSION_ID,
        },
        body: JSON.stringify({ query, top_k: topK }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || `Chat failed: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Chat failed';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function clearSession(): Promise<void> {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/books`, {
        method: 'DELETE',
        headers: {
          'session-id': SESSION_ID,
        },
      });

      if (!response.ok) {
        throw new Error(`Clear failed: ${response.status}`);
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Clear failed';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return {
    loading,
    error,
    uploadBooks,
    getBooks,
    deleteBook,
    chat,
    clearSession,
    sessionId: SESSION_ID,
  };
}
