<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue';
import type { Message } from '../types';
import ChatMessage from './ChatMessage.vue';
import { useApi } from '../composables/useApi';

interface Props {
  hasBooks: boolean;
}

const props = defineProps<Props>();

const { chat, loading, error } = useApi();

const messages = ref<Message[]>([]);
const queryInput = ref('');
const topK = ref(5);
const messagesContainer = ref<HTMLElement | null>(null);

const canSendMessage = computed(() => {
  return props.hasBooks && queryInput.value.trim().length > 0 && !loading.value;
});

watch(
  () => props.hasBooks,
  (newValue) => {
    if (!newValue) {
      messages.value = [];
    }
  }
);

async function scrollToBottom() {
  await nextTick();
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

async function handleSendMessage() {
  if (!canSendMessage.value) return;

  const query = queryInput.value.trim();
  queryInput.value = '';

  const userMessage: Message = {
    id: crypto.randomUUID(),
    role: 'user',
    content: query,
    timestamp: new Date(),
  };

  messages.value.push(userMessage);
  await scrollToBottom();

  try {
    const response = await chat(query, topK.value);

    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: response.answer,
      sources: response.sources,
      timestamp: new Date(),
    };

    messages.value.push(assistantMessage);
    await scrollToBottom();
  } catch (err) {
    const errorMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: `Error: ${err instanceof Error ? err.message : 'Failed to get response'}`,
      timestamp: new Date(),
    };

    messages.value.push(errorMessage);
    await scrollToBottom();
  }
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    handleSendMessage();
  }
}

function clearChat() {
  if (messages.value.length > 0 && confirm('Clear chat history?')) {
    messages.value = [];
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow flex flex-col h-[600px]">
    <div class="border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold">Chat</h2>
        <div class="flex items-center space-x-4">
          <div class="flex items-center space-x-2">
            <label for="topK" class="text-sm text-gray-600">
              Top K:
            </label>
            <input
              id="topK"
              v-model.number="topK"
              type="number"
              min="1"
              max="20"
              class="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
            />
          </div>
          <button
            v-if="messages.length > 0"
            @click="clearChat"
            type="button"
            class="text-sm text-gray-600 hover:text-gray-800"
          >
            Clear
          </button>
        </div>
      </div>
    </div>

    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto px-6 py-4 space-y-4 scroll-smooth"
    >
      <div v-if="!hasBooks" class="h-full flex items-center justify-center">
        <div class="text-center text-gray-500">
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
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <p class="mt-2">Upload books to start chatting</p>
        </div>
      </div>

      <div v-else-if="messages.length === 0" class="h-full flex items-center justify-center">
        <div class="text-center text-gray-500">
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
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
          <p class="mt-2">Ask a question about your books</p>
        </div>
      </div>

      <ChatMessage
        v-for="message in messages"
        :key="message.id"
        :message="message"
      />

      <div v-if="loading" class="flex justify-start">
        <div class="bg-gray-100 rounded-lg px-4 py-3">
          <div class="flex items-center space-x-2">
            <div class="animate-pulse flex space-x-1">
              <div class="h-2 w-2 bg-gray-400 rounded-full"></div>
              <div class="h-2 w-2 bg-gray-400 rounded-full animation-delay-200"></div>
              <div class="h-2 w-2 bg-gray-400 rounded-full animation-delay-400"></div>
            </div>
            <span class="text-sm text-gray-600">Thinking...</span>
          </div>
        </div>
      </div>

      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
        <p class="text-sm text-red-800">{{ error }}</p>
      </div>
    </div>

    <div class="border-t border-gray-200 px-6 py-4">
      <form @submit.prevent="handleSendMessage" class="flex space-x-2">
        <textarea
          v-model="queryInput"
          @keydown="handleKeyDown"
          placeholder="Ask a question about your books..."
          :disabled="!hasBooks || loading"
          rows="2"
          class="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        ></textarea>
        <button
          type="submit"
          :disabled="!canSendMessage"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors self-end"
        >
          <svg
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.animation-delay-200 {
  animation-delay: 0.2s;
}

.animation-delay-400 {
  animation-delay: 0.4s;
}
</style>
