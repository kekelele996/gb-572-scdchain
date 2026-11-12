<script setup lang="ts">
import { computed } from 'vue';
import type { BuildRun } from '@/types/build';
import EmptyState from './EmptyState.vue';
import StatusSeal from './StatusSeal.vue';

const props = defineProps<{ run: BuildRun | null }>();

const checks = computed(() => {
  const invariants = props.run?.invariants;
  if (!invariants) return [];
  return [
    { key: 'uniqueness', title: '每键唯一当前链', data: invariants.uniqueness, hint: 'Σ is_current = 1' },
    { key: 'overlap', title: '区间不重叠', data: invariants.overlap, hint: 'next.valid_from > prev.valid_to' },
    { key: 'gap', title: '区间无空洞', data: invariants.gap, hint: 'next.valid_from = prev.valid_to + 1' },
    { key: 'order', title: '区间有序', data: invariants.order, hint: 'valid_from ≤ valid_to' },
  ];
});

function ratio(passed: number, total: number): number {
  if (!total) return 0;
  return Math.round((passed / total) * 100);
}
</script>

<template>
  <div>
    <EmptyState v-if="!run" title="暂无校验报告" text="先在构建运行页发起一次构建，四个拉链不变量会在这里出报表。" />
    <template v-else>
      <div class="spread" style="margin-bottom: 10px">
        <p class="small muted">
          批次 #{{ run.run_no }} · {{ run.label }} · 输入指纹
          <span class="mono">{{ run.input_hash.slice(0, 12) }}</span>
        </p>
        <StatusSeal
          :label="run.invariants?.all_passed ? '全部通过' : '存在失败项'"
          :tone="run.invariants?.all_passed ? 'seal--ok' : 'seal--bad'"
        />
      </div>
      <div class="check-row" v-for="check in checks" :key="check.key">
        <div>
          <div>{{ check.title }}</div>
          <div class="small muted">{{ check.hint }}</div>
        </div>
        <div class="check-bar">
          <div
            class="check-bar__fill"
            :class="{ 'check-bar__fill--bad': check.data.passed !== check.data.total }"
            :style="{ width: `${ratio(check.data.passed, check.data.total)}%` }"
          />
        </div>
        <div class="check-row__state" :style="{ color: check.data.passed === check.data.total ? 'var(--sage)' : 'var(--danger)' }">
          {{ check.data.passed }} / {{ check.data.total }}
        </div>
      </div>
      <p v-if="!run.invariants?.all_passed" class="small" style="margin-top: 10px; color: var(--danger)">
        失败业务键：
        {{
          [
            ...(run.invariants?.uniqueness.failed_keys || []),
            ...(run.invariants?.gap.failed_keys || []),
            ...(run.invariants?.overlap.failed_keys || []),
          ]
            .filter((value, index, list) => list.indexOf(value) === index)
            .slice(0, 8)
            .join('、') || '—'
        }}
      </p>
      <div class="grid-stats" style="margin-top: 16px">
        <div class="stat">
          <span class="stat__label">迟到回插</span>
          <span class="stat__value">{{ run.stats.late_arrivals }}</span>
          <span class="stat__note">乱序到达后按日期回填</span>
        </div>
        <div class="stat">
          <span class="stat__label">同日折叠</span>
          <span class="stat__value">{{ run.stats.collapsed_same_day }}</span>
          <span class="stat__note">同键同日多源合一</span>
        </div>
        <div class="stat">
          <span class="stat__label">忽略列</span>
          <span class="stat__value" style="font-size: 1rem; padding-top: 6px">
            {{ run.stats.ignored_columns?.join(' / ') || '无' }}
          </span>
          <span class="stat__note">不参与变更判定</span>
        </div>
      </div>
    </template>
  </div>
</template>
