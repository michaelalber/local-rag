# Phase 7: Vue.js Frontend

## Objective

Build a minimal, functional UI: file upload, book list, and chat interface.

## Project Setup

```bash
cd localbookchat

# Create Vue project with Vite
npm create vite@latest frontend -- --template vue-ts

cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

## Files to Create

```
frontend/
├── index.html
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── style.css
│   ├── composables/
│   │   └── useApi.ts
│   ├── components/
│   │   ├── FileUpload.vue
│   │   ├── BookList.vue
│   │   ├── ChatInterface.vue
│   │   ├── ChatMessage.vue
│   │   └── SourceCitation.vue
│   └── types/
│       └── index.ts
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Configuration Files

### tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### src/style.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom styles */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
```

### vite.config.ts

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

## Implementation

### src/types/index.ts

```typescript
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
```

### src/composables/useApi.ts

```typescript
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
```

### src/components/FileUpload.vue

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';

const emit = defineEmits<{
  upload: [files: File[]];
}>();

const props = defineProps<{
  loading: boolean;
  maxFiles: number;
}>();

const dragOver = ref(false);
const selectedFiles = ref<File[]>([]);
const fileInput = ref<HTMLInputElement>();

const canUpload = computed(() => 
  selectedFiles.value.length > 0 && 
  selectedFiles.value.length <= props.maxFiles &&
  !props.loading
);

function handleDrop(event: DragEvent) {
  dragOver.value = false;
  const files = Array.from(event.dataTransfer?.files || []);
  addFiles(files);
}

function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files || []);
  addFiles(files);
}

function addFiles(files: File[]) {
  const validFiles = files.filter(f => 
    f.name.endsWith('.pdf') || f.name.endsWith('.epub')
  );
  
  const remaining = props.maxFiles - selectedFiles.value.length;
  selectedFiles.value.push(...validFiles.slice(0, remaining));
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1);
}

function handleUpload() {
  if (canUpload.value) {
    emit('upload', selectedFiles.value);
    selectedFiles.value = [];
  }
}

function openFilePicker() {
  fileInput.value?.click();
}
</script>

<template>
  <div class="space-y-4">
    <!-- Drop zone -->
    <div
      class="border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer"
      :class="[
        dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400',
        loading ? 'opacity-50 cursor-not-allowed' : ''
      ]"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="handleDrop"
      @click="openFilePicker"
    >
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".pdf,.epub"
        class="hidden"
        @change="handleFileSelect"
      />
      
      <div class="text-gray-600">
        <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
          <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <p class="mt-2">
          <span class="font-medium text-blue-600">Click to upload</span>
          or drag and drop
        </p>
        <p class="text-sm text-gray-500">PDF or EPUB (max {{ maxFiles }} files)</p>
      </div>
    </div>

    <!-- Selected files -->
    <div v-if="selectedFiles.length > 0" class="space-y-2">
      <div
        v-for="(file, index) in selectedFiles"
        :key="index"
        class="flex items-center justify-between bg-gray-50 rounded px-3 py-2"
      >
        <span class="text-sm truncate">{{ file.name }}</span>
        <button
          type="button"
          class="text-red-500 hover:text-red-700 ml-2"
          @click.stop="removeFile(index)"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <button
        type="button"
        class="w-full bg-blue-600 text-white rounded-lg py-2 px-4 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        :disabled="!canUpload"
        @click="handleUpload"
      >
        <span v-if="loading">Uploading...</span>
        <span v-else>Upload {{ selectedFiles.length }} file(s)</span>
      </button>
    </div>
  </div>
</template>
```

### src/components/BookList.vue

```vue
<script setup lang="ts">
import type { Book } from '../types';

defineProps<{
  books: Book[];
  loading: boolean;
}>();

const emit = defineEmits<{
  delete: [bookId: string];
  clear: [];
}>();

function formatFileType(type: string): string {
  return type.toUpperCase();
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="font-medium text-gray-900">Loaded Books ({{ books.length }})</h3>
      <button
        v-if="books.length > 0"
        type="button"
        class="text-sm text-red-600 hover:text-red-800"
        @click="emit('clear')"
      >
        Clear all
      </button>
    </div>

    <div v-if="books.length === 0" class="text-gray-500 text-sm py-4 text-center">
      No books loaded. Upload some books to get started.
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="book in books"
        :key="book.id"
        class="bg-white border rounded-lg p-3 flex items-start justify-between"
      >
        <div class="min-w-0 flex-1">
          <p class="font-medium text-gray-900 truncate">{{ book.title }}</p>
          <p v-if="book.author" class="text-sm text-gray-500 truncate">{{ book.author }}</p>
          <div class="flex items-center gap-2 mt-1">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
              {{ formatFileType(book.file_type) }}
            </span>
            <span class="text-xs text-gray-500">{{ book.chunk_count }} chunks</span>
          </div>
        </div>
        
        <button
          type="button"
          class="ml-2 text-gray-400 hover:text-red-500 transition-colors"
          :disabled="loading"
          @click="emit('delete', book.id)"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
```

### src/components/SourceCitation.vue

```vue
<script setup lang="ts">
import { ref } from 'vue';
import type { Source } from '../types';

defineProps<{
  sources: Source[];
}>();

const expanded = ref(false);
</script>

<template>
  <div v-if="sources.length > 0" class="mt-2">
    <button
      type="button"
      class="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
      @click="expanded = !expanded"
    >
      <svg
        class="h-4 w-4 transition-transform"
        :class="{ 'rotate-90': expanded }"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
      {{ sources.length }} source(s)
    </button>
    
    <div v-if="expanded" class="mt-2 space-y-2">
      <div
        v-for="(source, index) in sources"
        :key="index"
        class="bg-gray-50 rounded p-3 text-sm"
      >
        <div class="flex items-center gap-2 text-xs text-gray-500 mb-1">
          <span v-if="source.page_number">Page {{ source.page_number }}</span>
          <span v-if="source.chapter">{{ source.chapter }}</span>
        </div>
        <p class="text-gray-700 whitespace-pre-wrap">{{ source.content }}</p>
      </div>
    </div>
  </div>
</template>
```

### src/components/ChatMessage.vue

```vue
<script setup lang="ts">
import type { Message } from '../types';
import SourceCitation from './SourceCitation.vue';

defineProps<{
  message: Message;
}>();

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
</script>

<template>
  <div
    class="flex"
    :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <div
      class="max-w-[80%] rounded-lg px-4 py-2"
      :class="[
        message.role === 'user' 
          ? 'bg-blue-600 text-white' 
          : 'bg-gray-100 text-gray-900'
      ]"
    >
      <p class="whitespace-pre-wrap">{{ message.content }}</p>
      
      <SourceCitation
        v-if="message.sources && message.sources.length > 0"
        :sources="message.sources"
      />
      
      <p
        class="text-xs mt-1"
        :class="message.role === 'user' ? 'text-blue-200' : 'text-gray-500'"
      >
        {{ formatTime(message.timestamp) }}
      </p>
    </div>
  </div>
</template>
```

### src/components/ChatInterface.vue

```vue
<script setup lang="ts">
import { ref, nextTick, watch } from 'vue';
import type { Message, ChatResponse } from '../types';
import ChatMessage from './ChatMessage.vue';

const props = defineProps<{
  loading: boolean;
  disabled: boolean;
}>();

const emit = defineEmits<{
  send: [query: string];
}>();

const messages = ref<Message[]>([]);
const inputText = ref('');
const messagesContainer = ref<HTMLDivElement>();

function sendMessage() {
  if (!inputText.value.trim() || props.loading || props.disabled) return;
  
  const userMessage: Message = {
    id: crypto.randomUUID(),
    role: 'user',
    content: inputText.value.trim(),
    timestamp: new Date(),
  };
  
  messages.value.push(userMessage);
  emit('send', inputText.value.trim());
  inputText.value = '';
  
  scrollToBottom();
}

function addResponse(response: ChatResponse) {
  const assistantMessage: Message = {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: response.answer,
    sources: response.sources,
    timestamp: new Date(),
  };
  
  messages.value.push(assistantMessage);
  scrollToBottom();
}

function addError(error: string) {
  const errorMessage: Message = {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: `Error: ${error}`,
    timestamp: new Date(),
  };
  
  messages.value.push(errorMessage);
  scrollToBottom();
}

async function scrollToBottom() {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
}

// Expose methods for parent component
defineExpose({ addResponse, addError });
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Messages area -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin"
    >
      <div v-if="messages.length === 0" class="text-center text-gray-500 py-8">
        <p>No messages yet.</p>
        <p class="text-sm mt-1">Upload some books and start asking questions!</p>
      </div>
      
      <ChatMessage
        v-for="message in messages"
        :key="message.id"
        :message="message"
      />
      
      <!-- Loading indicator -->
      <div v-if="loading" class="flex justify-start">
        <div class="bg-gray-100 rounded-lg px-4 py-2">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
            <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Input area -->
    <div class="border-t p-4">
      <div class="flex gap-2">
        <textarea
          v-model="inputText"
          class="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          :disabled="disabled || loading"
          rows="2"
          placeholder="Ask a question about your books..."
          @keydown="handleKeydown"
        ></textarea>
        
        <button
          type="button"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-end"
          :disabled="!inputText.trim() || disabled || loading"
          @click="sendMessage"
        >
          Send
        </button>
      </div>
      
      <p v-if="disabled" class="text-sm text-amber-600 mt-2">
        Upload at least one book to start chatting.
      </p>
    </div>
  </div>
</template>
```

### src/App.vue

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useApi } from './composables/useApi';
import type { Book, ChatResponse } from './types';
import FileUpload from './components/FileUpload.vue';
import BookList from './components/BookList.vue';
import ChatInterface from './components/ChatInterface.vue';

const { loading, error, uploadBooks, getBooks, deleteBook, chat, clearSession } = useApi();

const books = ref<Book[]>([]);
const chatRef = ref<InstanceType<typeof ChatInterface>>();

const hasBooks = computed(() => books.value.length > 0);
const maxBooks = 5;

onMounted(async () => {
  try {
    books.value = await getBooks();
  } catch {
    // Session might not exist yet, that's fine
  }
});

async function handleUpload(files: File[]) {
  try {
    const newBooks = await uploadBooks(files);
    books.value.push(...newBooks);
  } catch (err) {
    console.error('Upload failed:', err);
  }
}

async function handleDelete(bookId: string) {
  try {
    await deleteBook(bookId);
    books.value = books.value.filter(b => b.id !== bookId);
  } catch (err) {
    console.error('Delete failed:', err);
  }
}

async function handleClear() {
  try {
    await clearSession();
    books.value = [];
  } catch (err) {
    console.error('Clear failed:', err);
  }
}

async function handleChat(query: string) {
  try {
    const response = await chat(query);
    chatRef.value?.addResponse(response);
  } catch (err) {
    chatRef.value?.addError(err instanceof Error ? err.message : 'Chat failed');
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <h1 class="text-xl font-bold text-gray-900">LocalBookChat</h1>
        <p class="text-sm text-gray-500">Chat with your eBooks locally</p>
      </div>
    </header>
    
    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Sidebar: Upload & Books -->
        <div class="lg:col-span-1 space-y-6">
          <!-- Upload Section -->
          <div class="bg-white rounded-lg shadow p-4">
            <h2 class="font-medium text-gray-900 mb-3">Upload Books</h2>
            <FileUpload
              :loading="loading"
              :max-files="maxBooks - books.length"
              @upload="handleUpload"
            />
          </div>
          
          <!-- Book List -->
          <div class="bg-white rounded-lg shadow p-4">
            <BookList
              :books="books"
              :loading="loading"
              @delete="handleDelete"
              @clear="handleClear"
            />
          </div>
        </div>
        
        <!-- Chat Area -->
        <div class="lg:col-span-2">
          <div class="bg-white rounded-lg shadow h-[600px]">
            <ChatInterface
              ref="chatRef"
              :loading="loading"
              :disabled="!hasBooks"
              @send="handleChat"
            />
          </div>
        </div>
      </div>
      
      <!-- Error display -->
      <div
        v-if="error"
        class="fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded"
      >
        {{ error }}
      </div>
    </main>
  </div>
</template>
```

### src/main.ts

```typescript
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

createApp(App).mount('#app')
```

## Verification

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Should open at http://localhost:5173
# Ensure backend is running: uvicorn src.api.main:app --reload --port 8000

# Test the flow:
# 1. Upload a PDF or EPUB
# 2. Verify it appears in the book list
# 3. Ask a question in the chat
# 4. Verify response with sources
# 5. Delete a book
# 6. Clear session
```

## Commit

```bash
git add .
git commit -m "feat: implement Vue.js frontend with upload, books, and chat UI"
```

## Next Phase

Proceed to `docs/phases/PHASE_8_POLISH.md`
