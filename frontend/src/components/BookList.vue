<script setup lang="ts">
import type { Book } from '../types';

interface Props {
  books: Book[];
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

const emit = defineEmits<{
  delete: [bookId: string];
  clearAll: [];
}>();

function handleDelete(bookId: string) {
  if (confirm('Are you sure you want to delete this book?')) {
    emit('delete', bookId);
  }
}

function handleClearAll() {
  if (confirm('Are you sure you want to delete all books? This will clear your session.')) {
    emit('clearAll');
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow p-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-semibold">Loaded Books</h2>
      <button
        v-if="books.length > 0"
        @click="handleClearAll"
        type="button"
        :disabled="loading"
        class="text-sm text-red-600 hover:text-red-800 disabled:text-gray-400"
      >
        Clear All
      </button>
    </div>

    <div v-if="books.length === 0" class="text-center py-8 text-gray-500">
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
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
      <p class="mt-2">No books loaded</p>
      <p class="text-sm mt-1">Upload some books to get started</p>
    </div>

    <ul v-else class="space-y-3">
      <li
        v-for="book in books"
        :key="book.id"
        class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <h3 class="font-medium text-gray-900 truncate">
              {{ book.title }}
            </h3>
            <p v-if="book.author" class="text-sm text-gray-600 mt-1">
              {{ book.author }}
            </p>
            <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
              <span class="flex items-center">
                <svg class="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fill-rule="evenodd"
                    d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                    clip-rule="evenodd"
                  />
                </svg>
                {{ book.file_type.toUpperCase() }}
              </span>
              <span class="flex items-center">
                <svg class="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z"
                  />
                </svg>
                {{ book.chunk_count }} chunks
              </span>
            </div>
          </div>

          <button
            @click="handleDelete(book.id)"
            type="button"
            :disabled="loading"
            class="ml-4 text-red-600 hover:text-red-800 disabled:text-gray-400 flex-shrink-0"
            aria-label="Delete book"
          >
            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>
