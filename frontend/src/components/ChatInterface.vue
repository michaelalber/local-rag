<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted } from 'vue';
import { TransitionGroup, Dialog, DialogPanel, DialogTitle } from '@headlessui/vue';
import { PaperAirplaneIcon, CpuChipIcon, XMarkIcon } from '@heroicons/vue/24/solid';
import type { Message } from '../types';
import ChatMessage from './ChatMessage.vue';
import ConfirmDialog from './ConfirmDialog.vue';
import { useApi } from '../composables/useApi';

interface Props {
  hasBooks: boolean;
}

interface OllamaModel {
  id: string;
  name: string;
  description: string;
  best_for: string[];
  size: string;
}

const props = defineProps<Props>();

const { chat, getModels, loading, error } = useApi();

const messages = ref<Message[]>([]);
const queryInput = ref('');
const topK = ref(5);
const messagesContainer = ref<HTMLElement | null>(null);
const showClearChatDialog = ref(false);
const showModelSelector = ref(false);
const availableModels = ref<OllamaModel[]>([]);
const selectedModel = ref<string | null>(
  sessionStorage.getItem('selectedModel') || null
);
const defaultModel = ref<string>('mistral:7b-instruct-q4_K_M');

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

onMounted(async () => {
  try {
    const response = await getModels();
    availableModels.value = response.models;
    defaultModel.value = response.default;
  } catch (err) {
    console.error('Failed to fetch models:', err);
  }
});

const currentModelName = computed(() => {
  const model = availableModels.value.find(m => m.id === selectedModel.value);
  return model?.name || 'Default Model';
});

function selectModel(modelId: string) {
  selectedModel.value = modelId;
  sessionStorage.setItem('selectedModel', modelId);
  showModelSelector.value = false;
}

function resetToDefault() {
  selectedModel.value = null;
  sessionStorage.removeItem('selectedModel');
  showModelSelector.value = false;
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
    // Build conversation history (excluding the current message)
    const history = messages.value.slice(0, -1).map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    const response = await chat(
      query,
      topK.value,
      history,
      selectedModel.value || undefined
    );

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
  if (messages.value.length > 0) {
    showClearChatDialog.value = true;
  }
}

function confirmClearChat() {
  messages.value = [];
}
</script>

<template>
  <div class="bg-white rounded-lg shadow flex flex-col h-[600px]">
    <div class="border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold">Chat</h2>
        <div class="flex items-center space-x-4">
          <button
            @click="showModelSelector = true"
            type="button"
            class="flex items-center space-x-1 px-3 py-1 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            title="Select Model"
          >
            <CpuChipIcon class="h-4 w-4" />
            <span>{{ currentModelName }}</span>
          </button>
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

      <TransitionGroup
        enter-active-class="transition ease-out duration-300"
        enter-from-class="opacity-0 translate-y-4"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-200"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
        move-class="transition duration-300"
      >
        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :message="message"
        />
      </TransitionGroup>

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
          <PaperAirplaneIcon class="h-5 w-5" />
        </button>
      </form>
    </div>

    <!-- Confirm Dialog -->
    <ConfirmDialog
      :open="showClearChatDialog"
      title="Clear Chat History"
      message="Are you sure you want to clear all messages? This action cannot be undone."
      confirm-text="Clear"
      type="warning"
      @confirm="confirmClearChat"
      @close="showClearChatDialog = false"
    />

    <!-- Model Selector Modal -->
    <Dialog :open="showModelSelector" @close="showModelSelector = false" class="relative z-50">
      <div class="fixed inset-0 bg-black/30" aria-hidden="true" />

      <div class="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel class="mx-auto max-w-4xl w-full bg-white rounded-xl shadow-2xl max-h-[80vh] flex flex-col">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <DialogTitle class="text-xl font-semibold text-gray-900">
              Select Language Model
            </DialogTitle>
            <button
              @click="showModelSelector = false"
              class="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon class="h-6 w-6" />
            </button>
          </div>

          <!-- Model Grid -->
          <div class="flex-1 overflow-y-auto p-6">
            <div v-if="availableModels.length === 0" class="text-center py-12 text-gray-500">
              <CpuChipIcon class="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>No models available. Is Ollama running?</p>
            </div>

            <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Default Model Card -->
              <button
                @click="resetToDefault"
                class="text-left p-4 border-2 rounded-lg transition-all hover:shadow-lg"
                :class="selectedModel === null
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'"
              >
                <div class="flex items-start justify-between mb-2">
                  <div>
                    <h3 class="font-semibold text-gray-900">Default Model</h3>
                    <p class="text-xs text-gray-500 mt-1">{{ defaultModel }}</p>
                  </div>
                  <div v-if="selectedModel === null" class="flex-shrink-0">
                    <svg class="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </div>
                <p class="text-sm text-gray-600 mb-3">Use the configured default model</p>
                <div class="flex flex-wrap gap-1">
                  <span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                    Recommended
                  </span>
                </div>
              </button>

              <!-- Available Models -->
              <button
                v-for="model in availableModels"
                :key="model.id"
                @click="selectModel(model.id)"
                class="text-left p-4 border-2 rounded-lg transition-all hover:shadow-lg"
                :class="selectedModel === model.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'"
              >
                <div class="flex items-start justify-between mb-2">
                  <div>
                    <h3 class="font-semibold text-gray-900">{{ model.name }}</h3>
                    <p class="text-xs text-gray-500 mt-1">{{ model.size }}</p>
                  </div>
                  <div v-if="selectedModel === model.id" class="flex-shrink-0">
                    <svg class="h-5 w-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </div>

                <p class="text-sm text-gray-600 mb-3">{{ model.description }}</p>

                <div class="space-y-2">
                  <div>
                    <p class="text-xs font-medium text-gray-700 mb-1">Best for:</p>
                    <div class="flex flex-wrap gap-1">
                      <span
                        v-for="use in model.best_for"
                        :key="use"
                        class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs"
                      >
                        {{ use }}
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            </div>
          </div>

          <!-- Footer -->
          <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
            <p class="text-sm text-gray-600">
              Selected model will be used for all future queries in this session.
            </p>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
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
