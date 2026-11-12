<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import AppShell from '@/components/common/AppShell.vue';
import PaperPanel from '@/components/common/PaperPanel.vue';
import StatusSeal from '@/components/common/StatusSeal.vue';
import InvariantReport from '@/components/common/InvariantReport.vue';
import TimelineAxis from '@/components/common/TimelineAxis.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import ErrorNotice from '@/components/common/ErrorNotice.vue';
import { useAuthStore } from '@/stores/auth';
import { useBuildStore } from '@/stores/build';
import { BUILD_STATUS_LABELS, BUILD_STATUS_TONE } from '@/constants/buildStatus';
import { formatDateTime, durationSeconds } from '@/utils/formatDate';
import { ATTRIBUTE_LABELS } from '@/constants/attributes';

const auth = useAuthStore();
const store = useBuildStore();

const notice = ref('');
const showForm = ref(false);
const notes = ref('人工触发：核对冲突裁决后的重建');
const baselineId = ref<number | null>(null);

const snapshotDates = computed(() => store.detail?.stats?.snapshot_dates || []);
const compareReady = computed(() => Boolean(store.compare));
const defaultBaseline = computed(() => {
  const succeeded = store.succeededRuns;
  if (succeeded.length < 2) return null;
  return succeeded[1]?.id || null;
});

onMounted(async () => {
  await store.loadRuns();
  if (defaultBaseline.value) baselineId.value = defaultBaseline.value;
});

async function startBuild() {
  notice.value = '';
  try {
    const run = await store.create(notes.value);
    notice.value = `批次 #${run.run_no} 已提交到 Celery 队列，正在等待 worker…`;
    const finished = await store.pollUntilDone(run.id);
    if (finished.status === 'succeeded') {
      notice.value = `批次 #${finished.run_no} 完成：${finished.stats.chains_total} 条链，新增 ${finished.stats.new_chains} 条，不变量 ${finished.invariants.all_passed ? '全部通过' : '存在失败'}。`;
      const previous = finished.previous_run_id;
      if (previous) await store.loadCompare(previous, finished.id);
    } else {
      notice.value = `批次 #${finished.run_no} 状态：${BUILD_STATUS_LABELS[finished.status]} ${finished.error_message || ''}`;
    }
    await store.loadRuns();
  } catch (err) {
    notice.value = err instanceof Error ? err.message : '发起构建失败';
  }
}

async function runCompare() {
  if (!store.detail || !baselineId.value) return;
  await store.loadCompare(baselineId.value, store.detail.id);
}

function attrLabel(key: string): string {
  return ATTRIBUTE_LABELS[key] || key;
}
</script>

<template>
  <AppShell>
    <header class="page__head reveal">
      <div>
        <p class="eyebrow">第二章 · Build</p>
        <h1 class="page__title">构建运行</h1>
        <p class="page__kicker">
          每晚快照入库后重新拉链：关旧链、开新链、折叠同日变更、回插迟到快照；四个不变量在写库前校验。
        </p>
      </div>
      <div class="page__meta">
        最近批次：{{ store.runs[0] ? `#${store.runs[0].run_no} ${BUILD_STATUS_LABELS[store.runs[0].status]}` : '—' }}<br />
        触发权限：{{ auth.canRunBuild ? '可发起' : '只读（auditor 会被 403）' }}
      </div>
    </header>

    <div class="page__body">
      <ErrorNotice v-if="store.error" :message="store.error" @retry="store.loadRuns()" />
      <p v-if="notice" class="note-line">{{ notice }}</p>

      <div class="split split--runs">
        <PaperPanel title="批次编年" kicker="Build chronicle" hint="按运行顺序倒排">
          <template #actions>
            <button class="btn btn--primary btn--small" type="button" :disabled="!auth.canRunBuild" @click="showForm = !showForm">
              {{ showForm ? '收起' : '发起构建' }}
            </button>
          </template>

          <form v-if="showForm" class="stack" style="margin-bottom: 14px" @submit.prevent="startBuild">
            <div class="field">
              <span class="field__label">批次说明</span>
              <input v-model="notes" class="input" maxlength="200" />
            </div>
            <button class="btn btn--rust btn--small" type="submit" :disabled="store.creating">
              {{ store.creating ? '提交中…' : '提交到 worker' }}
            </button>
            <p v-if="!auth.canRunBuild" class="small muted">当前角色不能发起构建（服务端 403）。</p>
          </form>

          <div v-if="store.loading && !store.runs.length" class="loading">读取批次列表…</div>
          <EmptyState v-else-if="!store.runs.length" title="还没有构建批次" text="seed 会写入 v1 / v2 两个批次；也可以由 admin 或 modeler 手动发起。" />
          <div v-else class="stack">
            <button
              v-for="run in store.runs"
              :key="run.id"
              type="button"
              class="conflict"
              style="text-align: left; cursor: pointer; width: 100%"
              :style="{ borderLeftColor: run.id === store.detail?.id ? 'var(--rust)' : 'var(--rule)' }"
              @click="store.select(run.id)"
            >
              <div class="spread">
                <strong class="numeral">No. {{ run.run_no }}</strong>
                <StatusSeal :label="BUILD_STATUS_LABELS[run.status]" :tone="BUILD_STATUS_TONE[run.status]" />
              </div>
              <p class="small">{{ run.label }}</p>
              <p class="small muted">
                {{ formatDateTime(run.finished_at || run.started_at) }} ·
                {{ run.stats.chains_total ?? 0 }} 条链 ·
                新增 {{ run.stats.new_chains ?? 0 }}
              </p>
            </button>
          </div>
        </PaperPanel>

        <div class="stack">
          <PaperPanel title="批次统计" kicker="Batch statistics" :hint="store.detail?.notes || ''">
            <template #actions>
              <StatusSeal
                v-if="store.detail"
                :label="BUILD_STATUS_LABELS[store.detail.status]"
                :tone="BUILD_STATUS_TONE[store.detail.status]"
              />
            </template>
            <div v-if="!store.detail" class="loading">选择一个批次查看统计…</div>
            <template v-else>
              <div class="grid-stats">
                <div class="stat">
                  <span class="stat__label">拉链总数</span>
                  <span class="stat__value">{{ store.detail.stats.chains_total }}</span>
                  <span class="stat__note">180 业务键</span>
                </div>
                <div class="stat">
                  <span class="stat__label">关旧链</span>
                  <span class="stat__value">{{ store.detail.stats.chains_closed }}</span>
                  <span class="stat__note">变更观察日次日生效</span>
                </div>
                <div class="stat">
                  <span class="stat__label">变更客户</span>
                  <span class="stat__value">{{ store.detail.stats.changed_keys }}</span>
                  <span class="stat__note">等级 / 机构</span>
                </div>
                <div class="stat">
                  <span class="stat__label">迟到回插</span>
                  <span class="stat__value">{{ store.detail.stats.late_arrivals }}</span>
                  <span class="stat__note">乱序快照</span>
                </div>
                <div class="stat">
                  <span class="stat__label">同日折叠</span>
                  <span class="stat__value">{{ store.detail.stats.collapsed_same_day }}</span>
                  <span class="stat__note">多源同日合一</span>
                </div>
                <div class="stat">
                  <span class="stat__label">人工覆盖链</span>
                  <span class="stat__value">{{ store.detail.stats.overrides_applied }}</span>
                  <span class="stat__note">source=manual</span>
                </div>
                <div class="stat">
                  <span class="stat__label">冲突候选</span>
                  <span class="stat__value">{{ store.detail.stats.conflicts_detected }}</span>
                  <span class="stat__note">自动 {{ store.detail.stats.conflicts_auto_resolved }} · 待裁 {{ store.detail.stats.conflicts_open }}</span>
                </div>
                <div class="stat">
                  <span class="stat__label">较上批新增</span>
                  <span class="stat__value">{{ store.detail.stats.new_chains ?? 0 }}</span>
                  <span class="stat__note">新开链数</span>
                </div>
              </div>
              <p class="small muted" style="margin-top: 12px">
                输入指纹 <span class="mono">{{ store.detail.input_hash.slice(0, 24) }}…</span> ·
                耗时 {{ durationSeconds(store.detail.started_at, store.detail.finished_at) ?? '—' }}s ·
                触发人 {{ store.detail.triggered_by }}
              </p>
            </template>
          </PaperPanel>

          <PaperPanel title="快照时间轴" kicker="Snapshot axis" hint="本批次参与拉链的每日全量快照">
            <TimelineAxis v-if="snapshotDates.length" :dates="snapshotDates" :active="store.detail?.stats.as_of_cutoff || undefined" />
            <div v-else class="loading">选择批次后显示时间轴</div>
          </PaperPanel>

          <PaperPanel title="拉链不变量校验" kicker="Invariants" hint="写库后立即复核：唯一当前链 / 不重叠 / 无空洞 / 有序">
            <InvariantReport :run="store.detail" />
          </PaperPanel>

          <PaperPanel title="批次对比" kicker="Run diff" hint="左选基线、右为当前批次，比较新增链与当前值变化">
            <template #actions>
              <select v-model.number="baselineId" class="select" style="min-width: 160px">
                <option :value="null" disabled>选择基线批次</option>
                <option v-for="run in store.succeededRuns" :key="run.id" :value="run.id" :disabled="run.id === store.detail?.id">
                  #{{ run.run_no }} {{ run.label }}
                </option>
              </select>
              <button class="btn btn--small" type="button" :disabled="!baselineId || !store.detail" @click="runCompare">对比</button>
            </template>
            <EmptyState v-if="!compareReady" title="尚未对比" text="选一个基线批次点「对比」，能看到人工覆盖重建带来的新增链。" />
            <template v-else-if="store.compare">
              <div class="grid-stats">
                <div class="stat">
                  <span class="stat__label">新增链</span>
                  <span class="stat__value" style="color: var(--rust)">{{ store.compare.new_chains }}</span>
                  <span class="stat__note">右侧独有</span>
                </div>
                <div class="stat">
                  <span class="stat__label">消失链</span>
                  <span class="stat__value">{{ store.compare.removed_chains }}</span>
                  <span class="stat__note">左侧独有</span>
                </div>
                <div class="stat">
                  <span class="stat__label">当前值变化</span>
                  <span class="stat__value">{{ store.compare.changed_keys }}</span>
                  <span class="stat__note">裁决覆盖生效</span>
                </div>
              </div>
              <table v-if="store.compare.new_chain_samples.length" class="ledger" style="margin-top: 12px">
                <thead>
                  <tr>
                    <th>业务键</th>
                    <th>生效日</th>
                    <th>变更字段</th>
                    <th>来源</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="sample in store.compare.new_chain_samples" :key="`${sample.business_key}-${sample.valid_from}`">
                    <td class="ledger__key">{{ sample.business_key }}</td>
                    <td class="mono">{{ sample.valid_from }}</td>
                    <td class="small">{{ sample.change_fields.map(attrLabel).join(' / ') }}</td>
                    <td class="small">{{ sample.version_source }}</td>
                  </tr>
                </tbody>
              </table>
              <p v-else class="small muted">两批次链集合一致（幂等重跑）。</p>
            </template>
          </PaperPanel>
        </div>
      </div>
    </div>
  </AppShell>
</template>
