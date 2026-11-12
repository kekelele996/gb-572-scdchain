<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import AppShell from '@/components/common/AppShell.vue';
import PaperPanel from '@/components/common/PaperPanel.vue';
import ConflictCard from '@/components/common/ConflictCard.vue';
import InvariantReport from '@/components/common/InvariantReport.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import ErrorNotice from '@/components/common/ErrorNotice.vue';
import StatusSeal from '@/components/common/StatusSeal.vue';
import PaginationBar from '@/components/common/PaginationBar.vue';
import { useAuthStore } from '@/stores/auth';
import { useConflictStore } from '@/stores/conflict';
import { useAsyncResource } from '@/hooks/useAsyncResource';
import { fetchOverview } from '@/api/meta';
import type { Overview } from '@/types/overview';
import type { ConflictRow } from '@/types/conflict';

const auth = useAuthStore();
const store = useConflictStore();
const router = useRouter();
const { data: overviewData, error: overviewError, run: loadOverview } = useAsyncResource<Overview>(null);
const pageNo = ref(1);

const summary = computed(() => store.summary);
const latestRun = computed(() => overviewData.value?.latest_run || null);
const strategyEntries = computed(() => {
  const labels = summary.value?.labels.strategy || {};
  return Object.entries(summary.value?.by_strategy || {})
    .filter(([key]) => key !== 'open')
    .map(([key, value]) => ({ key, label: labels[key] || key, value }));
});

async function load() {
  await store.load(pageNo.value, 8);
}

async function resolve(row: ConflictRow, strategy: 'candidate' | 'manual', value: string, note: string) {
  try {
    await store.resolve(row, strategy, value, note);
  } catch {
    /* error surfaced by store */
  }
}

function changeTab(next: 'open' | 'all') {
  pageNo.value = 1;
  store.setStatus(next);
}

onMounted(async () => {
  await Promise.all([load(), loadOverview(() => fetchOverview())]);
});
</script>

<template>
  <AppShell>
    <header class="page__head reveal">
      <div>
        <p class="eyebrow">第五章 · Adjudication</p>
        <h1 class="page__title">冲突裁决与校验报告</h1>
        <p class="page__kicker">
          同一天同一业务键，三个系统给出不同写法或不同值时先归一化；归一后仍冲突的进入裁决队列，人工决定会留痕并在重建时生效。
        </p>
      </div>
      <div class="page__meta">
        待裁决：{{ summary?.open ?? '—' }} / 全部 {{ summary?.total ?? '—' }}<br />
        裁决权限：{{ auth.canResolve ? '可提交' : '只读（服务端 403）' }}
      </div>
    </header>

    <div class="page__body">
      <ErrorNotice v-if="store.error" :message="store.error" @retry="load()" />
      <ErrorNotice v-if="overviewError" :message="overviewError" @retry="loadOverview(() => fetchOverview())" />
      <p v-if="store.notice" class="note-line">
        {{ store.notice }}
        <button class="btn btn--small" type="button" style="margin-left: 10px" @click="router.push('/builds')">去重建批次</button>
      </p>

      <div v-if="summary" class="grid-stats">
        <div class="stat">
          <span class="stat__label">归一后一致</span>
          <span class="stat__value">{{ summary.by_verdict.normalized_equal || 0 }}</span>
          <span class="stat__note">手机号 / 机构编码写法差异</span>
        </div>
        <div class="stat">
          <span class="stat__label">同音近似</span>
          <span class="stat__value">{{ summary.by_verdict.similar || 0 }}</span>
          <span class="stat__note">姓名拼音收敛</span>
        </div>
        <div class="stat">
          <span class="stat__label">真实冲突</span>
          <span class="stat__value" style="color: var(--rust)">{{ summary.by_verdict.conflict || 0 }}</span>
          <span class="stat__note">需人工裁定</span>
        </div>
        <div class="stat">
          <span class="stat__label">已裁决</span>
          <span class="stat__value">
            {{ (summary.by_status.resolved || 0) + (summary.by_status.manual || 0) }}
          </span>
          <span class="stat__note">含自动收敛</span>
        </div>
      </div>

      <div class="split" style="grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr)">
        <PaperPanel title="冲突队列" kicker="Adjudication queue" hint="待裁决优先；裁决结果按次日生效写入拉链">
          <template #actions>
            <div class="tabs">
              <button class="tab" :class="{ 'is-active': store.status === 'open' }" type="button" @click="changeTab('open')">
                待裁决 {{ summary?.open ?? '' }}
              </button>
              <button class="tab" :class="{ 'is-active': store.status === 'all' }" type="button" @click="changeTab('all')">
                全部 {{ summary?.total ?? '' }}
              </button>
            </div>
          </template>

          <div v-if="store.loading && !store.page" class="loading">读取冲突队列…</div>
          <EmptyState
            v-else-if="!store.page || !store.page.items.length"
            :title="store.status === 'open' ? '待裁决队列已清空' : '还没有冲突项'"
            text="归一化能自动收敛的写法差异不计入队列；真实冲突才会出现在这里。"
          />
          <div v-else class="stack">
            <ConflictCard
              v-for="row in store.page.items"
              :key="row.id"
              :conflict="row"
              :resolving="store.resolvingId === row.id"
              :can-resolve="auth.canResolve"
              @resolve="(strategy, value, note) => resolve(row, strategy, value, note)"
            />
            <PaginationBar
              :page="store.page.page"
              :pages="store.page.pages"
              :total="store.page.total"
              :page-size="store.page.page_size"
              @change="pageNo = $event; load()"
            />
          </div>
        </PaperPanel>

        <div class="stack">
          <PaperPanel title="拉链校验报告" kicker="Invariant report" hint="最新成功批次的四项不变量">
            <InvariantReport :run="latestRun" />
          </PaperPanel>

          <PaperPanel title="裁决策略统计" kicker="Strategies" hint="自动收敛与人工裁决的分布">
            <div v-if="!strategyEntries.length" class="loading">暂无裁决记录</div>
            <div v-else class="stack" style="gap: 8px">
              <div v-for="item in strategyEntries" :key="item.key" class="spread small">
                <span>{{ item.label }}</span>
                <span class="numeral">{{ item.value }}</span>
              </div>
            </div>
            <p class="small muted" style="margin-top: 10px">
              自动收敛只在归一后（或同音相似度 ≥ 0.85）执行；不会静默改值，候选、来源与时间都写在冲突项里。
            </p>
          </PaperPanel>

          <PaperPanel title="裁决动作说明" kicker="How it applies">
            <div class="stack" style="gap: 8px">
              <p class="small">
                1. 在候选中裁定：取候选来源的归一值，记录策略 <code>candidate</code>。
              </p>
              <p class="small">
                2. 人工覆盖：可填候选之外的值，记录策略 <code>manual</code> 与依据。
              </p>
              <p class="small muted">
                3. 两条路径都会生成 <code>effective_date = 冲突日 + 1</code> 的覆盖，重建后追加
                <code>version_source = manual</code> 的新链，旧链照常保留。
              </p>
              <StatusSeal :label="latestRun ? `基线 #${latestRun.run_no}` : '暂无批次'" tone="seal--navy" />
            </div>
          </PaperPanel>
        </div>
      </div>
    </div>
  </AppShell>
</template>
