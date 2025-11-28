<script setup lang="ts">
import { computed } from 'vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js/lib/core';
import 'highlight.js/styles/github.css';

// Import languages for code highlighting
import javascript from 'highlight.js/lib/languages/javascript';
import typescript from 'highlight.js/lib/languages/typescript';
import python from 'highlight.js/lib/languages/python';
import java from 'highlight.js/lib/languages/java';
import cpp from 'highlight.js/lib/languages/cpp';
import csharp from 'highlight.js/lib/languages/csharp';
import go from 'highlight.js/lib/languages/go';
import rust from 'highlight.js/lib/languages/rust';
import sql from 'highlight.js/lib/languages/sql';
import json from 'highlight.js/lib/languages/json';
import xml from 'highlight.js/lib/languages/xml';
import bash from 'highlight.js/lib/languages/bash';

import type { Message } from '../types';
import SourceCitation from './SourceCitation.vue';

// Register languages
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('python', python);
hljs.registerLanguage('java', java);
hljs.registerLanguage('cpp', cpp);
hljs.registerLanguage('csharp', csharp);
hljs.registerLanguage('go', go);
hljs.registerLanguage('rust', rust);
hljs.registerLanguage('sql', sql);
hljs.registerLanguage('json', json);
hljs.registerLanguage('xml', xml);
hljs.registerLanguage('bash', bash);

interface Props {
  message: Message;
}

const props = defineProps<Props>();

// Initialize markdown-it with syntax highlighting
const md = new MarkdownIt({
  html: false, // Disable HTML tags for security
  linkify: true, // Auto-convert URLs to links
  typographer: true, // Enable smart quotes and other typographic replacements
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang, ignoreIllegals: true }).value;
      } catch (e) {
        console.error('Highlight error:', e);
      }
    }
    return ''; // Use default escaping
  }
});

const formattedContent = computed(() => {
  if (props.message.role === 'user') {
    return props.message.content;
  }
  // For assistant messages, render markdown
  return md.render(props.message.content);
});

function formatTime(date: Date): string {
  return new Date(date).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>

<template>
  <div
    :class="[
      'flex',
      message.role === 'user' ? 'justify-end' : 'justify-start'
    ]"
  >
    <div
      :class="[
        'max-w-3xl rounded-lg px-4 py-3',
        message.role === 'user'
          ? 'bg-blue-600 text-white'
          : 'bg-gray-100 text-gray-900'
      ]"
    >
      <div class="flex items-start space-x-2">
        <div class="flex-shrink-0">
          <div
            :class="[
              'h-8 w-8 rounded-full flex items-center justify-center',
              message.role === 'user' ? 'bg-blue-700' : 'bg-gray-300'
            ]"
          >
            <svg
              v-if="message.role === 'user'"
              class="h-5 w-5 text-white"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                clip-rule="evenodd"
              />
            </svg>
            <svg
              v-else
              class="h-5 w-5 text-gray-600"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3zM3.31 9.397L5 10.12v4.102a8.969 8.969 0 00-1.05-.174 1 1 0 01-.89-.89 11.115 11.115 0 01.25-3.762zM9.3 16.573A9.026 9.026 0 007 14.935v-3.957l1.818.78a3 3 0 002.364 0l5.508-2.361a11.026 11.026 0 01.25 3.762 1 1 0 01-.89.89 8.968 8.968 0 00-5.35 2.524 1 1 0 01-1.4 0zM6 18a1 1 0 001-1v-2.065a8.935 8.935 0 00-2-.712V17a1 1 0 001 1z"
              />
            </svg>
          </div>
        </div>

        <div class="flex-1 min-w-0">
          <!-- User messages: plain text -->
          <p
            v-if="message.role === 'user'"
            class="text-sm whitespace-pre-wrap break-words"
          >
            {{ message.content }}
          </p>

          <!-- Assistant messages: rendered markdown with syntax highlighting -->
          <div
            v-else
            class="prose prose-sm max-w-none text-sm text-gray-900"
            v-html="formattedContent"
          ></div>

          <div v-if="message.sources && message.sources.length > 0" class="mt-3 space-y-2">
            <p class="text-xs font-semibold text-gray-600 mb-2">Sources:</p>
            <SourceCitation
              v-for="(source, index) in message.sources"
              :key="index"
              :source="source"
              :index="index"
            />
          </div>

          <p
            :class="[
              'text-xs mt-2',
              message.role === 'user' ? 'text-blue-200' : 'text-gray-500'
            ]"
          >
            {{ formatTime(message.timestamp) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
