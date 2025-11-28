<script setup lang="ts">
import { computed } from 'vue';
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue';
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

function getSourceTitle(): string {
  const parts: string[] = [];

  if (props.source.chapter) {
    parts.push(props.source.chapter);
  }

  if (props.source.page_number !== null) {
    parts.push(`p. ${props.source.page_number}`);
  }

  if (props.source.has_code && props.source.code_language) {
    parts.push(`(${props.source.code_language})`);
  }

  return parts.join(' · ');
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
  <Popover class="relative inline-block">
    <PopoverButton
      class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 transition-colors"
    >
      [{{ index + 1 }}]
    </PopoverButton>

    <PopoverPanel
      class="absolute z-10 mt-2 w-96 max-w-sm bg-white rounded-lg shadow-lg border border-gray-200 focus:outline-none"
    >
      <div class="p-4">
        <div class="text-xs font-semibold text-gray-900 mb-2">
          {{ getSourceTitle() }}
        </div>
        <div
          v-if="source.has_code"
          class="text-xs text-gray-700 leading-relaxed prose prose-sm max-w-none overflow-auto max-h-64"
          v-html="formattedContent"
        ></div>
        <p
          v-else
          class="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed overflow-auto max-h-64"
        >
          {{ source.content }}
        </p>
      </div>
    </PopoverPanel>
  </Popover>
</template>
