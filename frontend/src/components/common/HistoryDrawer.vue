<script setup lang="ts">
import type { ChainHistory } from '@/types/dim';
import { formatDateTime } from '@/utils/formatDate';
import ChainTimeline from './ChainTimeline.vue';
import EmptyState from './EmptyState.vue';

defineProps<{ history: ChainHistory | null; loading: boolean }>();
const emit = defineEmits<{ close: [] }>();
</script>

<template>
  <div class="drawer-backdrop" @click.self="emit('close')">
    <aside class="drawer" role="dialog" aria-label="客户编年条目">
      <div class="spread" style="margin-bottom: 16px">
        <div>
          <p class="eyebrow">Chronicle entry · 编年条目</p>
          <h2 class="page__title" style="font-size: var(--step-2)">
            {{ history?.business_key || '…' }}
          </h2>
        </div>
        <button class="btn btn--small" type="button" @click="emit('close')">关闭</button>
      </div>

      <div v-if="loading" class="loading">正在读取拉链与裁决记录…</div>
      <EmptyState v-else-if="!history" title="没有编年记录" text="该业务键在最近构建中不存在，请先在当前维度页选择一条。" />
      <template v-else>
        <p class="small muted" style="margin-bottom: 10px">
          当前批次 #{{ history.run.run_no }} · {{ history.run.label }} · 共 {{ history.versions.length }} 条链
        </p>
        <ChainTimeline :versions="history.versions" />

        <h3 class="panel__title" style="margin-top: 22px; font-size: 1rem">裁决记录</h3>
        <p v-if="!history.conflicts.length" class="small muted">该客户没有跨源冲突，三系统当日取值一致。</p>
        <div v-for="conflict in history.conflicts" :key="conflict.id" class="note-line" style="margin-top: 8px">
          {{ conflict.attribute_key }} · {{ conflict.status }} · {{ conflict.verdict }}
          <template v-if="conflict.resolution.value">
            → {{ conflict.resolution.value }}（{{ conflict.resolution.strategy }}）
          </template>
        </div>

        <h3 class="panel__title" style="margin-top: 22px; font-size: 1rem">上游快照</h3>
        <table class="ledger" style="margin-top: 8px">
          <thead>
            <tr>
              <th>日期</th>
              <th>来源</th>
              <th>等级</th>
              <th>机构</th>
              <th>到达</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in history.snapshots" :key="`${row.source_code}-${row.snapshot_date}`">
              <td class="mono">{{ row.snapshot_date }}</td>
              <td>{{ row.source_code }}</td>
              <td>{{ row.attributes.customer_level }}</td>
              <td class="mono">{{ row.attributes.org_code }}</td>
              <td class="mono small">
                {{ formatDateTime(row.ingested_at) }}
                <span v-if="row.is_late" style="color: var(--rust)">迟到</span>
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </aside>
  </div>
</template>
