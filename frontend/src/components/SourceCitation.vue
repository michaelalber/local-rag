<script setup lang="ts">
import { ref } from 'vue';
import type { Source } from '../types';

interface Props {
  source: Source;
  index: number;
}

const props = defineProps<Props>();

const isExpanded = ref(false);

function toggleExpanded() {
  isExpanded.value = !isExpanded.value;
}

function getSourceLabel(): string {
  const parts: string[] = [`[${props.index + 1}]`];

  if (props.source.chapter) {
    parts.push(props.source.chapter);
  }

  if (props.source.page_number !== null) {
    parts.push(`p. ${props.source.page_number}`);
  }

  return parts.join(' ');
}
</script>

<template>
  <div class="border border-gray-200 rounded-lg overflow-hidden">
    <button
      @click="toggleExpanded"
      type="button"
      class="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left flex items-center justify-between transition-colors"
    >
      <span class="font-medium text-sm text-gray-700">
        {{ getSourceLabel() }}
      </span>
      <svg
        :class="['h-5 w-5 text-gray-500 transition-transform', isExpanded && 'rotate-180']"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>

    <div
      v-if="isExpanded"
      class="px-4 py-3 bg-white border-t border-gray-200"
    >
      <p class="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
        {{ source.content }}
      </p>
    </div>
  </div>
</template>
