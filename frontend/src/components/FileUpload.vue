<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  maxBooks: number;
  currentBookCount: number;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

const emit = defineEmits<{
  upload: [files: File[]];
}>();

const selectedFiles = ref<File[]>([]);
const isDragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

const ALLOWED_TYPES = [
  'application/pdf',
  'application/epub+zip',
  'text/markdown',
  'text/plain',
  'text/x-rst',
  'text/html',
];
const MAX_SIZE_MB = 50;

const remainingSlots = computed(() => props.maxBooks - props.currentBookCount);
const canAddMore = computed(() => remainingSlots.value > 0);

function validateFile(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type) && !file.name.match(/\.(pdf|epub|md|txt|rst|html|htm)$/i)) {
    return `${file.name}: Only PDF, EPUB, Markdown, Text, RST, and HTML files are supported`;
  }

  const sizeMB = file.size / (1024 * 1024);
  if (sizeMB > MAX_SIZE_MB) {
    return `${file.name}: File size exceeds ${MAX_SIZE_MB}MB limit`;
  }

  return null;
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files) {
    addFiles(Array.from(target.files));
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false;

  if (event.dataTransfer?.files) {
    addFiles(Array.from(event.dataTransfer.files));
  }
}

function addFiles(files: File[]) {
  if (!canAddMore.value) {
    alert(`Maximum of ${props.maxBooks} books allowed`);
    return;
  }

  const validFiles: File[] = [];
  const errors: string[] = [];

  for (const file of files) {
    const error = validateFile(file);
    if (error) {
      errors.push(error);
    } else {
      validFiles.push(file);
    }
  }

  if (errors.length > 0) {
    alert(errors.join('\n'));
  }

  const totalCount = selectedFiles.value.length + validFiles.length + props.currentBookCount;
  if (totalCount > props.maxBooks) {
    const allowed = props.maxBooks - props.currentBookCount - selectedFiles.value.length;
    alert(`Can only add ${allowed} more file(s)`);
    selectedFiles.value.push(...validFiles.slice(0, allowed));
  } else {
    selectedFiles.value.push(...validFiles);
  }

  if (fileInput.value) {
    fileInput.value.value = '';
  }
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1);
}

function handleUpload() {
  if (selectedFiles.value.length > 0) {
    emit('upload', selectedFiles.value);
    selectedFiles.value = [];
  }
}

function triggerFileInput() {
  fileInput.value?.click();
}

function handleDragOver(event: DragEvent) {
  event.preventDefault();
  isDragging.value = true;
}

function handleDragLeave() {
  isDragging.value = false;
}
</script>

<template>
  <div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-xl font-semibold mb-4">Upload Books</h2>

    <div
      @drop.prevent="handleDrop"
      @dragover.prevent="handleDragOver"
      @dragleave="handleDragLeave"
      @click="triggerFileInput"
      :class="[
        'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
        isDragging
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400',
        !canAddMore && 'opacity-50 cursor-not-allowed'
      ]"
    >
      <input
        ref="fileInput"
        type="file"
        multiple
        accept=".pdf,.epub,.md,.txt,.rst,.html,.htm,application/pdf,application/epub+zip,text/markdown,text/plain,text/x-rst,text/html"
        @change="handleFileSelect"
        class="hidden"
        :disabled="!canAddMore"
      />

      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        stroke="currentColor"
        fill="none"
        viewBox="0 0 48 48"
        aria-hidden="true"
      >
        <path
          d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>

      <p class="mt-2 text-sm text-gray-600">
        <span class="font-semibold">Click to upload</span> or drag and drop
      </p>
      <p class="text-xs text-gray-500 mt-1">
        PDF, EPUB, Markdown, Text, RST, or HTML files (max {{ MAX_SIZE_MB }}MB each)
      </p>
      <p class="text-xs text-gray-500">
        {{ remainingSlots }} slot(s) available
      </p>
    </div>

    <div v-if="selectedFiles.length > 0" class="mt-4">
      <h3 class="text-sm font-medium text-gray-700 mb-2">Selected Files:</h3>
      <ul class="space-y-2">
        <li
          v-for="(file, index) in selectedFiles"
          :key="index"
          class="flex items-center justify-between bg-gray-50 rounded px-3 py-2"
        >
          <div class="flex items-center space-x-2 flex-1 min-w-0">
            <svg
              class="h-5 w-5 text-gray-400 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                clip-rule="evenodd"
              />
            </svg>
            <span class="text-sm text-gray-700 truncate">{{ file.name }}</span>
            <span class="text-xs text-gray-500 flex-shrink-0">
              ({{ (file.size / 1024 / 1024).toFixed(2) }} MB)
            </span>
          </div>
          <button
            @click="removeFile(index)"
            type="button"
            class="ml-2 text-red-600 hover:text-red-800 flex-shrink-0"
            :disabled="loading"
          >
            <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </li>
      </ul>

      <button
        @click="handleUpload"
        type="button"
        :disabled="loading || selectedFiles.length === 0"
        class="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
      >
        <span v-if="loading">Uploading...</span>
        <span v-else>Upload {{ selectedFiles.length }} file(s)</span>
      </button>
    </div>
  </div>
</template>
