<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import type { Book } from './types';
import { useApi } from './composables/useApi';
import FileUpload from './components/FileUpload.vue';
import BookList from './components/BookList.vue';
import ChatInterface from './components/ChatInterface.vue';

const { uploadBooks, getBooks, deleteBook, clearSession, loading, sessionId } = useApi();

const books = ref<Book[]>([]);
const uploadError = ref<string | null>(null);

const MAX_BOOKS = 5;

const hasBooks = computed(() => books.value.length > 0);

onMounted(async () => {
  await loadBooks();
});

async function loadBooks() {
  try {
    books.value = await getBooks();
  } catch (err) {
    console.error('Failed to load books:', err);
  }
}

async function handleUpload(files: File[]) {
  uploadError.value = null;

  try {
    const newBooks = await uploadBooks(files);
    books.value.push(...newBooks);
  } catch (err) {
    uploadError.value = err instanceof Error ? err.message : 'Upload failed';
  }
}

async function handleDelete(bookId: string) {
  try {
    await deleteBook(bookId);
    books.value = books.value.filter(book => book.id !== bookId);
  } catch (err) {
    console.error('Failed to delete book:', err);
    alert('Failed to delete book');
  }
}

async function handleClearAll() {
  try {
    await clearSession();
    books.value = [];
  } catch (err) {
    console.error('Failed to clear session:', err);
    alert('Failed to clear session');
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-3">
            <svg
              class="h-8 w-8 text-blue-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            <h1 class="text-2xl font-bold text-gray-900">LocalBookChat</h1>
          </div>
          <div class="text-xs text-gray-500 font-mono">
            Session: {{ sessionId.substring(0, 8) }}...
          </div>
        </div>
      </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-1 space-y-6">
          <FileUpload
            :max-books="MAX_BOOKS"
            :current-book-count="books.length"
            :loading="loading"
            @upload="handleUpload"
          />

          <div v-if="uploadError" class="bg-red-50 border border-red-200 rounded-lg p-4">
            <p class="text-sm text-red-800">{{ uploadError }}</p>
          </div>

          <BookList
            :books="books"
            :loading="loading"
            @delete="handleDelete"
            @clear-all="handleClearAll"
          />
        </div>

        <div class="lg:col-span-2">
          <ChatInterface :has-books="hasBooks" />
        </div>
      </div>
    </main>

    <footer class="mt-12 border-t border-gray-200 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <p class="text-center text-sm text-gray-500">
          LocalBookChat - Privacy-focused eBook RAG using local models
        </p>
        <p class="text-center text-xs text-gray-400 mt-1">
          All data stays on your machine. No external API calls.
        </p>
      </div>
    </footer>
  </div>
</template>
