<script setup lang="ts">
import { ref, computed } from 'vue';
import hljs from 'highlight.js/lib/core';
import 'highlight.js/styles/github.css';

// Import commonly used languages
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
import markdown from 'highlight.js/lib/languages/markdown';

import type { Source } from '../types';

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
hljs.registerLanguage('markdown', markdown);

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

  if (props.source.has_code && props.source.code_language) {
    parts.push(`(${props.source.code_language})`);
  }

  return parts.join(' ');
}

const formattedContent = computed(() => {
  if (!props.source.has_code) {
    return props.source.content;
  }

  // Try to highlight code blocks
  const content = props.source.content;
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)\n```/g;

  return content.replace(codeBlockRegex, (match, lang, code) => {
    try {
      const language = lang || props.source.code_language || 'plaintext';
      const highlighted = hljs.highlight(code, { language, ignoreIllegals: true });
      return `<pre><code class="hljs">${highlighted.value}</code></pre>`;
    } catch (e) {
      return `<pre><code>${code}</code></pre>`;
    }
  });
});
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
      <div
        v-if="source.has_code"
        class="text-sm text-gray-700 leading-relaxed prose prose-sm max-w-none"
        v-html="formattedContent"
      ></div>
      <p
        v-else
        class="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed"
      >
        {{ source.content }}
      </p>
    </div>
  </div>
</template>
