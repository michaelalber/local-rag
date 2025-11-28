import { ref } from 'vue';
import type { Book, ChatResponse } from '../types';

// Generate session ID once per browser session
const SESSION_ID = sessionStorage.getItem('sessionId') || crypto.randomUUID();
sessionStorage.setItem('sessionId', SESSION_ID);

const API_BASE = '/api';

export interface UploadProgress {
  fileName: string;
  uploadProgress: number;
  stage: 'uploading' | 'processing';
  statusText: string;
}

export function useApi() {
  const loading = ref(false);
  const error = ref<string | null>(null);
  const uploadProgress = ref<UploadProgress | null>(null);

  async function uploadBooks(files: File[]): Promise<Book[]> {
    loading.value = true;
    error.value = null;

    try {
      const results: Book[] = [];

      // Process files one at a time to show accurate progress
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        uploadProgress.value = {
          fileName: file.name,
          uploadProgress: 0,
          stage: 'uploading',
          statusText: `Uploading ${file.name} (${i + 1}/${files.length})...`,
        };

        const formData = new FormData();
        formData.append('files', file);

        // Use XMLHttpRequest for upload progress tracking
        const books = await new Promise<Book[]>((resolve, reject) => {
          const xhr = new XMLHttpRequest();

          xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable && uploadProgress.value) {
              const percentComplete = (e.loaded / e.total) * 100;
              uploadProgress.value.uploadProgress = percentComplete;
            }
          });

          xhr.addEventListener('load', () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              // Upload complete, now processing
              if (uploadProgress.value) {
                uploadProgress.value.stage = 'processing';
                uploadProgress.value.uploadProgress = 100;
                uploadProgress.value.statusText = `Processing ${file.name}... (parsing, embedding, storing)`;
              }

              try {
                const data = JSON.parse(xhr.responseText);
                resolve(data);
              } catch (err) {
                reject(new Error('Failed to parse response'));
              }
            } else {
              try {
                const data = JSON.parse(xhr.responseText);
                reject(new Error(data.error || `Upload failed: ${xhr.status}`));
              } catch {
                reject(new Error(`Upload failed: ${xhr.status}`));
              }
            }
          });

          xhr.addEventListener('error', () => {
            reject(new Error('Network error during upload'));
          });

          xhr.open('POST', `${API_BASE}/books`);
          xhr.setRequestHeader('session-id', SESSION_ID);
          xhr.send(formData);
        });

        results.push(...books);
      }

      uploadProgress.value = null;
      return results;
    } catch (err) {
      uploadProgress.value = null;
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

  async function getModels() {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE}/models`);

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch models';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function chat(
    query: string,
    topK: number = 5,
    history: Array<{role: string, content: string}> = [],
    model?: string
  ): Promise<ChatResponse> {
    loading.value = true;
    error.value = null;

    try {
      const body: any = { query, top_k: topK, history };
      if (model) {
        body.model = model;
      }

      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'session-id': SESSION_ID,
        },
        body: JSON.stringify(body),
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
    uploadProgress,
    uploadBooks,
    getBooks,
    deleteBook,
    getModels,
    chat,
    clearSession,
    sessionId: SESSION_ID,
  };
}
