<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import AppShell from '@/components/common/AppShell.vue';
import PaperPanel from '@/components/common/PaperPanel.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import ErrorNotice from '@/components/common/ErrorNotice.vue';
import StatusSeal from '@/components/common/StatusSeal.vue';
import { useAuthStore } from '@/stores/auth';
import { useDimensionStore } from '@/stores/dimension';
import { NORMALIZATION_LABELS } from '@/constants/conflictStatus';
import { ROLE_LABELS } from '@/constants/roles';
import { formatDate } from '@/utils/formatDate';
import type { MergeRule } from '@/types/dimension';

const auth = useAuthStore();
const store = useDimensionStore();
const notice = ref('');
const drafts = reactive<Record<number, { priority: string[]; normalization: string; exclude: boolean }>>({});

function syncDrafts(rules: MergeRule[]) {
  for (const rule of rules) {
    drafts[rule.id] = {
      priority: [...rule.source_priority],
      normalization: rule.normalization,
      exclude: rule.exclude_from_change,
    };
  }
}

onMounted(async () => {
  await store.load();
  syncDrafts(store.rules);
});

function move(rule: MergeRule, index: number, delta: number) {
  if (!auth.canEditRules) return;
  const draft = drafts[rule.id];
  if (!draft) return;
  const target = index + delta;
  if (target < 0 || target >= draft.priority.length) return;
  const [item] = draft.priority.splice(index, 1);
  draft.priority.splice(target, 0, item);
}

function sourceName(code: string): string {
  return store.sources.find((source) => source.code === code)?.name || code;
}

async function save(rule: MergeRule) {
  const draft = drafts[rule.id];
  if (!draft) return;
  notice.value = '';
  try {
    await store.save(rule.id, {
      source_priority: draft.priority,
      normalization: draft.normalization,
      exclude_from_change: draft.exclude,
    });
    notice.value = `${rule.display_name} 的合并规则已保存（重建后生效）`;
  } catch (err) {
    notice.value = err instanceof Error ? err.message : '保存失败';
  }
}
</script>

<template>
  <AppShell>
    <header class="page__head reveal">
      <div>
        <p class="eyebrow">第一章 · Design</p>
        <h1 class="page__title">维度设计</h1>
        <p class="page__kicker">
          属性级合并规则：谁优先、怎么归一、哪些列不参与变更判定。规则改动会写进审计日志，下一次重建生效。
        </p>
      </div>
      <div class="page__meta">
        当前身份：{{ auth.user?.display_name }} · {{ ROLE_LABELS[auth.role] }}<br />
        规则编辑：{{ auth.canEditRules ? '可写' : '只读（服务端同样 403）' }}
      </div>
    </header>

    <div class="page__body">
      <ErrorNotice v-if="store.error" :message="store.error" @retry="store.load()" />
      <p v-if="notice" class="note-line">{{ notice }}</p>

      <PaperPanel
        title="合并规则台账"
        kicker="Merge rules"
        hint="优先级靠上的源在冲突时胜出；归一化决定「写法不同」是否算变更"
      >
        <template #actions>
          <StatusSeal :label="auth.canEditRules ? 'admin 可编辑' : '只读视图'" :tone="auth.canEditRules ? 'seal--navy' : 'seal--neutral'" />
        </template>
        <div v-if="store.loading" class="loading">正在读取规则台账…</div>
        <EmptyState v-else-if="!store.rules.length" title="暂无合并规则" text="seed 会写入 6 条默认规则；若为空请检查后端容器日志。" />
        <table v-else class="ledger">
          <thead>
            <tr>
              <th>属性</th>
              <th>类型</th>
              <th>源优先级（高 → 低）</th>
              <th>归一化</th>
              <th>变更判定</th>
              <th>保存</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rule in store.rules" :key="rule.id">
              <td>
                <div>{{ rule.display_name }}</div>
                <div class="small muted mono">{{ rule.attribute_key }}</div>
              </td>
              <td class="small">{{ rule.data_type }}</td>
              <td>
                <div class="chips">
                  <span v-for="(code, index) in drafts[rule.id]?.priority || rule.source_priority" :key="code" class="chip" :class="{ 'chip--strong': index === 0 }">
                    <span class="chip__order">{{ index + 1 }}</span>{{ sourceName(code) }}
                    <template v-if="auth.canEditRules">
                      <button class="small muted" type="button" style="border: none; background: none; cursor: pointer" @click="move(rule, index, -1)">↑</button>
                      <button class="small muted" type="button" style="border: none; background: none; cursor: pointer" @click="move(rule, index, 1)">↓</button>
                    </template>
                  </span>
                </div>
              </td>
              <td>
                <select v-if="auth.canEditRules" v-model="drafts[rule.id].normalization" class="select" style="min-width: 150px">
                  <option v-for="(label, key) in NORMALIZATION_LABELS" :key="key" :value="key">{{ label }}</option>
                </select>
                <span v-else class="small">{{ NORMALIZATION_LABELS[rule.normalization] || rule.normalization }}</span>
              </td>
              <td>
                <label v-if="auth.canEditRules" class="small row" style="gap: 6px">
                  <input v-model="drafts[rule.id].exclude" type="checkbox" />
                  忽略列
                </label>
                <StatusSeal v-else :label="rule.exclude_from_change ? '忽略列' : '参与判定'" :tone="rule.exclude_from_change ? 'seal--warn' : 'seal--neutral'" />
              </td>
              <td>
                <button v-if="auth.canEditRules" class="btn btn--small" type="button" :disabled="store.savingId === rule.id" @click="save(rule)">
                  {{ store.savingId === rule.id ? '保存中…' : '保存' }}
                </button>
                <span v-else class="small muted">只读</span>
              </td>
            </tr>
          </tbody>
        </table>
      </PaperPanel>

      <div class="split" style="grid-template-columns: minmax(0, 1fr) minmax(0, 1fr)">
        <PaperPanel title="源系统登记" kicker="Source systems" hint="可信度用于归一后仍冲突时的兜底参考">
          <div class="stack">
            <div v-for="source in store.sources" :key="source.code" class="conflict" style="border-left-color: var(--ink-3)">
              <div class="spread">
                <strong>{{ source.name }}</strong>
                <StatusSeal :label="`信任 ${source.trust_level}`" tone="seal--neutral" />
              </div>
              <p class="small muted">{{ source.description }}</p>
              <p class="small muted">
                接口人：{{ source.contact_owner }} · 每日快照 {{ source.snapshot_time }} · {{ source.system_type }}
              </p>
            </div>
          </div>
        </PaperPanel>

        <PaperPanel title="上游快照接入" kicker="Snapshot feed" hint="按日期 / 源系统统计当日入库行数">
          <div v-if="store.feed" class="stack">
            <p class="small muted">
              合计 {{ store.feed.summary.total_rows }} 行 · 覆盖
              {{ store.feed.summary.snapshot_dates.length }} 个快照日
            </p>
            <table class="ledger">
              <thead>
                <tr>
                  <th>快照日</th>
                  <th>来源</th>
                  <th>行数</th>
                  <th>迟到</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="batch in store.feed.summary.batches" :key="`${batch.snapshot_date}-${batch.source_code}`">
                  <td class="mono">{{ formatDate(batch.snapshot_date) }}</td>
                  <td>{{ sourceName(batch.source_code) }}</td>
                  <td class="numeral">{{ batch.rows }}</td>
                  <td class="numeral" :style="{ color: batch.late_rows ? 'var(--rust)' : 'inherit' }">{{ batch.late_rows }}</td>
                </tr>
              </tbody>
            </table>
            <p class="small muted">
              最近一条：{{ store.feed.rows[0]?.business_key }} · {{ store.feed.rows[0]?.source_name }} ·
              {{ store.feed.rows[0]?.snapshot_date }} 入库
            </p>
          </div>
          <div v-else class="loading">读取快照接入统计…</div>
        </PaperPanel>
      </div>
    </div>
  </AppShell>
</template>
