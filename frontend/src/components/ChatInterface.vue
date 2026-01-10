<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted } from 'vue';
import { TransitionGroup, Dialog, DialogPanel, DialogTitle } from '@headlessui/vue';
import { PaperAirplaneIcon, CpuChipIcon, XMarkIcon, ShieldCheckIcon, BookOpenIcon, SparklesIcon, AcademicCapIcon, GlobeAltIcon } from '@heroicons/vue/24/solid';
import type { Message, QuerySource, Source, MCPSource } from '../types';
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

// Icon mapping for MCP sources
const sourceIcons: Record<string, any> = {
  compliance: ShieldCheckIcon,
  mslearn: AcademicCapIcon,
  export_control: GlobeAltIcon,
};

const props = defineProps<Props>();

const { chatStream, healthCheck, getModels, loading, error } = useApi();

const messages = ref<Message[]>([]);
const queryInput = ref('');
const retrievalPercentage = ref(2.0);  // Default 2% retrieval for better coverage
const messagesContainer = ref<HTMLElement | null>(null);
const showClearChatDialog = ref(false);
const showModelSelector = ref(false);
const availableModels = ref<OllamaModel[]>([]);
const selectedModel = ref<string | null>(
  sessionStorage.getItem('selectedModel') || null
);
const defaultModel = ref<string>('mistral:7b-instruct-q4_K_M');

// Source selection - dynamic from health check
const selectedSource = ref<QuerySource>(
  (sessionStorage.getItem('selectedSource') as QuerySource) || 'books'
);
const mcpSources = ref<MCPSource[]>([]);

// Helper to check if an MCP source is available
function isMcpSourceAvailable(name: string): boolean {
  const source = mcpSources.value.find(s => s.name === name);
  return source?.available ?? false;
}

// Check if any MCP source is available
const anyMcpAvailable = computed(() => mcpSources.value.some(s => s.available));

// Check if source selection should allow sending
const canSendMessage = computed(() => {
  const hasQuery = queryInput.value.trim().length > 0 && !loading.value;
  if (!hasQuery) return false;

  // For books source, require books to be uploaded
  if (selectedSource.value === 'books') {
    return props.hasBooks;
  }
  // For specific MCP sources, check if available
  if (selectedSource.value === 'compliance' || selectedSource.value === 'mslearn' || selectedSource.value === 'export_control') {
    return isMcpSourceAvailable(selectedSource.value);
  }
  // For 'all' or 'both', require at least one source
  return props.hasBooks || anyMcpAvailable.value;
});

// Source options for the selector - built dynamically
const sourceOptions = computed(() => {
  const options = [
    {
      value: 'books' as QuerySource,
      label: 'Books',
      icon: BookOpenIcon,
      disabled: false,
      description: 'Search your uploaded books',
    },
  ];

  // Add MCP sources dynamically
  for (const source of mcpSources.value) {
    options.push({
      value: source.name as QuerySource,
      label: source.display_name,
      icon: sourceIcons[source.name] || SparklesIcon,
      disabled: !source.available,
      description: source.available
        ? `Search ${source.display_name}`
        : `${source.display_name} not available`,
    });
  }

  // Add "All" option if there are multiple sources
  if (mcpSources.value.length > 0) {
    options.push({
      value: 'all' as QuerySource,
      label: 'All',
      icon: SparklesIcon,
      disabled: !anyMcpAvailable.value && !props.hasBooks,
      description: 'Search all available sources',
    });
  }

  return options;
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
  // Fetch available models
  try {
    const response = await getModels();
    availableModels.value = response.models;
    defaultModel.value = response.default;
  } catch (err) {
    console.error('Failed to fetch models:', err);
  }

  // Fetch MCP sources from health check
  try {
    const health = await healthCheck();
    mcpSources.value = health.mcp_sources || [];
  } catch (err) {
    console.error('Failed to check health:', err);
    mcpSources.value = [];
  }
});

function selectSource(source: QuerySource) {
  selectedSource.value = source;
  sessionStorage.setItem('selectedSource', source);
}

const currentModelName = computed(() => {
  const model = availableModels.value.find(m => m.id === selectedModel.value);
  return model?.name || 'Default Model';
});

// Dynamic placeholder text based on selected source
const placeholderText = computed(() => {
  if (selectedSource.value === 'books') {
    return 'Ask a question about your books...';
  }
  if (selectedSource.value === 'all') {
    return 'Ask about your books and connected knowledge sources...';
  }
  // For MCP sources, use the display name
  const source = mcpSources.value.find(s => s.name === selectedSource.value);
  if (source) {
    return `Ask about ${source.display_name}...`;
  }
  return 'Ask a question...';
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

  // Create streaming assistant message
  const assistantMessageId = crypto.randomUUID();
  const assistantMessage: Message = {
    id: assistantMessageId,
    role: 'assistant',
    content: '',
    sources: [],
    timestamp: new Date(),
    isStreaming: true,
  };
  messages.value.push(assistantMessage);
  await scrollToBottom();

  try {
    // Build conversation history (excluding the current user message and streaming message)
    const history = messages.value.slice(0, -2).map(msg => ({
      role: msg.role,
      content: msg.content
    }));

    await chatStream(query, {
      onStart: () => {
        // Streaming started
      },
      onSources: (sourcesData) => {
        // Convert source data to Source objects
        const sources: Source[] = sourcesData.book_sources.map(s => ({
          content: s.content,
          page_number: s.page_number,
          chapter: s.chapter,
          book_id: s.book_id || '',
          has_code: false,
          code_language: null,
        }));
        const msg = messages.value.find(m => m.id === assistantMessageId);
        if (msg) {
          msg.sources = sources;
        }
      },
      onToken: async (token) => {
        const msg = messages.value.find(m => m.id === assistantMessageId);
        if (msg) {
          msg.content += token;
          await scrollToBottom();
        }
      },
      onDone: () => {
        const msg = messages.value.find(m => m.id === assistantMessageId);
        if (msg) {
          msg.isStreaming = false;
        }
      },
      onError: (errorMsg) => {
        const msg = messages.value.find(m => m.id === assistantMessageId);
        if (msg) {
          msg.content = `Error: ${errorMsg}`;
          msg.isStreaming = false;
        }
      },
    }, {
      history,
      model: selectedModel.value || undefined,
      retrievalPercentage: retrievalPercentage.value,
      source: selectedSource.value,
    });
  } catch (err) {
    const msg = messages.value.find(m => m.id === assistantMessageId);
    if (msg) {
      msg.content = `Error: ${err instanceof Error ? err.message : 'Failed to get response'}`;
      msg.isStreaming = false;
    }
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
  <div class="bg-white rounded-lg shadow flex flex-col h-[calc(100vh-12rem)] min-h-[600px]">
    <div class="border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold">Chat</h2>
        <div class="flex items-center space-x-4">
          <!-- Source Selector -->
          <div class="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
            <button
              v-for="option in sourceOptions"
              :key="option.value"
              @click="selectSource(option.value)"
              :disabled="option.disabled"
              :title="option.description"
              class="flex items-center space-x-1 px-3 py-1.5 text-sm rounded-md transition-all"
              :class="[
                selectedSource === option.value
                  ? 'bg-white text-blue-600 shadow-sm'
                  : option.disabled
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-600 hover:text-gray-900'
              ]"
            >
              <component :is="option.icon" class="h-4 w-4" />
              <span>{{ option.label }}</span>
            </button>
          </div>
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
            <label for="retrievalPercentage" class="text-sm text-gray-600" title="Percentage of document chunks to retrieve">
              Retrieval:
            </label>
            <input
              id="retrievalPercentage"
              v-model.number="retrievalPercentage"
              type="number"
              min="0.5"
              max="10.0"
              step="0.1"
              class="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
            />
            <span class="text-xs text-gray-500">%</span>
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
      <!-- Empty state: No books and books source selected -->
      <div v-if="selectedSource === 'books' && !hasBooks" class="h-full flex items-center justify-center">
        <div class="text-center text-gray-500">
          <BookOpenIcon class="mx-auto h-12 w-12 text-gray-400" />
          <p class="mt-2">Upload books to start chatting</p>
        </div>
      </div>

      <!-- Empty state: MCP source not available -->
      <div v-else-if="selectedSource !== 'books' && selectedSource !== 'all' && !isMcpSourceAvailable(selectedSource)" class="h-full flex items-center justify-center">
        <div class="text-center text-gray-500">
          <component :is="sourceIcons[selectedSource] || SparklesIcon" class="mx-auto h-12 w-12 text-gray-400" />
          <p class="mt-2">{{ selectedSource }} source is not configured</p>
          <p class="mt-1 text-sm">Enable the MCP source in your configuration</p>
        </div>
      </div>

      <!-- Empty state: All source but nothing available -->
      <div v-else-if="selectedSource === 'all' && !hasBooks && !anyMcpAvailable" class="h-full flex items-center justify-center">
        <div class="text-center text-gray-500">
          <SparklesIcon class="mx-auto h-12 w-12 text-gray-400" />
          <p class="mt-2">Upload books or configure MCP sources to start chatting</p>
        </div>
      </div>

      <!-- Ready to chat -->
      <div v-else-if="messages.length === 0" class="h-full flex items-center justify-center">
        <div class="text-center text-gray-500">
          <component
            :is="sourceIcons[selectedSource] || (selectedSource === 'books' ? BookOpenIcon : SparklesIcon)"
            class="mx-auto h-12 w-12 text-gray-400"
          />
          <p class="mt-2">
            <template v-if="selectedSource === 'books'">Ask a question about your books</template>
            <template v-else-if="selectedSource === 'all'">Ask about your books and connected knowledge sources</template>
            <template v-else>Ask about {{ mcpSources.find(s => s.name === selectedSource)?.display_name || selectedSource }}</template>
          </p>
          <p v-if="mcpSources.length > 0" class="mt-1 text-xs text-green-600">
            {{ mcpSources.filter(s => s.available).length }} MCP source(s) connected
          </p>
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

      <!-- Show streaming indicator when waiting for first token -->
      <div v-if="loading && messages.length > 0 && messages[messages.length - 1].content === ''" class="flex justify-start">
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
          :placeholder="placeholderText"
          :disabled="!canSendMessage && queryInput.trim().length === 0"
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
