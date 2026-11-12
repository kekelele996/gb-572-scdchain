<script setup lang="ts">
import { ref } from 'vue';
import type { ConflictRow } from '@/types/conflict';
import { CONFLICT_STATUS_LABELS, NORMALIZATION_LABELS } from '@/constants/conflictStatus';
import { formatDateTime } from '@/utils/formatDate';
import StatusSeal from './StatusSeal.vue';

const props = defineProps<{ conflict: ConflictRow; resolving: boolean; canResolve: boolean }>();
const emit = defineEmits<{ resolve: [strategy: 'candidate' | 'manual', value: string, note: string] }>();

const mode = ref<'candidate' | 'manual'>('candidate');
const chosen = ref(props.conflict.candidates[0]?.value || '');
const manual = ref('');
const note = ref('');
const localError = ref('');

const tone =
  props.conflict.status === 'open' ? 'seal--warn' : props.conflict.status === 'manual' ? 'seal--navy' : 'seal--ok';

function submit() {
  localError.value = '';
  const value = mode.value === 'manual' ? manual.value.trim() : chosen.value;
  if (!value) {
    localError.value = '请选择候选值或填写人工覆盖值';
    return;
  }
  emit('resolve', mode.value, value, note.value.trim());
}
</script>

<template>
  <article class="conflict" :class="{ 'conflict--resolved': conflict.status !== 'open' }">
    <header class="conflict__head">
      <div>
        <p class="eyebrow">{{ conflict.snapshot_date }} · 快照冲突窗口</p>
        <h3 class="conflict__title">
          {{ conflict.business_key }} · {{ conflict.display_name }}
          <span class="small muted">（{{ NORMALIZATION_LABELS[conflict.normalization] || conflict.normalization }}）</span>
        </h3>
      </div>
      <div class="row">
        <StatusSeal :label="conflict.verdict_label" :tone="conflict.verdict === 'conflict' ? 'seal--warn' : 'seal--neutral'" />
        <StatusSeal :label="CONFLICT_STATUS_LABELS[conflict.status] || conflict.status" :tone="tone" />
        <span class="small muted">相似度 {{ conflict.similarity.toFixed(2) }}</span>
      </div>
    </header>

    <table class="conflict__candidates">
      <thead>
        <tr>
          <th>来源</th>
          <th>原始值</th>
          <th>归一值</th>
          <th>观测时间</th>
          <th>可信度</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="candidate in conflict.candidates" :key="candidate.source_code">
          <td>{{ candidate.source_name || candidate.source_code }}</td>
          <td class="mono">{{ candidate.value }}</td>
          <td class="mono">{{ candidate.canonical }}</td>
          <td class="mono small">{{ formatDateTime(candidate.observed_at) }}</td>
          <td class="numeral">{{ candidate.trust }} / 3</td>
        </tr>
      </tbody>
    </table>

    <p v-if="conflict.status !== 'open'" class="note-line">
      裁决留痕：{{ conflict.strategy_label }} → <strong>{{ conflict.resolution.value }}</strong>
      <span v-if="conflict.resolution.note"> · {{ conflict.resolution.note }}</span>
      <span class="small muted">（{{ conflict.resolved_by }} {{ formatDateTime(conflict.resolved_at) }}，生效 {{ conflict.effective_date }}）</span>
    </p>

    <form v-else class="conflict__resolve" @submit.prevent="submit">
      <div class="field" style="min-width: 150px">
        <span class="field__label">裁决方式</span>
        <select v-model="mode" class="select">
          <option value="candidate">在候选中裁定</option>
          <option value="manual">人工覆盖（非候选值）</option>
        </select>
      </div>
      <div v-if="mode === 'candidate'" class="field" style="min-width: 200px">
        <span class="field__label">候选值</span>
        <select v-model="chosen" class="select">
          <option v-for="candidate in conflict.candidates" :key="candidate.source_code" :value="candidate.value">
            {{ candidate.value }} · {{ candidate.source_name || candidate.source_code }}
          </option>
        </select>
      </div>
      <div v-else class="field" style="min-width: 200px">
        <span class="field__label">覆盖值（1-64 字）</span>
        <input v-model="manual" class="input" placeholder="例如 金卡 / BJ01" maxlength="64" />
      </div>
      <div class="field toolbar__grow">
        <span class="field__label">裁决依据</span>
        <input v-model="note" class="input" placeholder="例如：以会员权益变更函为准" maxlength="200" />
      </div>
      <button class="btn btn--rust" type="submit" :disabled="resolving || !canResolve">
        {{ resolving ? '提交中…' : '提交裁决' }}
      </button>
      <p v-if="!canResolve" class="small muted">当前角色只读，无法提交裁决（服务端同样返回 403）</p>
      <p v-if="localError" class="form-error">{{ localError }}</p>
    </form>
  </article>
</template>
