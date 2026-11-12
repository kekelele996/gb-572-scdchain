<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import AppShell from '@/components/common/AppShell.vue';
import PaperPanel from '@/components/common/PaperPanel.vue';
import DimTable from '@/components/common/DimTable.vue';
import HistoryDrawer from '@/components/common/HistoryDrawer.vue';
import PaginationBar from '@/components/common/PaginationBar.vue';
import TimelineAxis from '@/components/common/TimelineAxis.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import ErrorNotice from '@/components/common/ErrorNotice.vue';
import StatusSeal from '@/components/common/StatusSeal.vue';
import { useDimStore } from '@/stores/dim';
import { useAsyncResource } from '@/hooks/useAsyncResource';
import { fetchOverview } from '@/api/meta';
import type { Overview } from '@/types/overview';
import type { DimRow } from '@/types/dim';
import { downloadCsv } from '@/utils/request';
import { formatDate } from '@/utils/formatDate';

const store = useDimStore();
const { data: overviewData, error: overviewError, run: loadOverview } = useAsyncResource<Overview>(null);
const asOf = ref('2026-11-05');
const pageNo = ref(1);
const drawerOpen = ref(false);
const selectedKey = ref('');
const downloadError = ref('');
const notice = ref('');

const dates = computed(() => overviewData.value?.snapshot_dates || []);
const demo = computed(() => overviewData.value?.asof_demo);

const demoHistory = computed(() => {
  if (!store.history || !demo.value || store.history.business_key !== demo.value.business_key) return null;
  return store.history;
});

const demoAsOfRow = computed(() => {
  const history = demoHistory.value;
  if (!history) return null;
  const day = asOf.value;
  return history.versions.find((version) => version.valid_from <= day && (!version.valid_to || version.valid_to >= day)) || null;
});

const demoCurrentRow = computed(() => {
  const history = demoHistory.value;
  if (!history) return null;
  return history.versions[history.versions.length - 1] || null;
});

function load() {
  store.loadAsOf(asOf.value, '', '', pageNo.value, 20);
}

function pick(date: string) {
  asOf.value = date;
  notice.value = `回溯日期已切换为 ${date}`;
}

function openHistory(row: DimRow) {
  selectedKey.value = row.business_key;
  drawerOpen.value = true;
  store.loadHistory(row.business_key);
}

async function exportCsv() {
  downloadError.value = '';
  try {
    await downloadCsv(`/dims/as-of/export?as_of=${encodeURIComponent(asOf.value)}`, `scdchain_asof_${asOf.value}.csv`);
    notice.value = `已导出 ${asOf.value} 的时点快照 CSV（每键一条当时有效链）`;
  } catch (err) {
    downloadError.value = err instanceof Error ? err.message : '导出失败';
  }
}

watch(asOf, () => {
  pageNo.value = 1;
  load();
});
watch(pageNo, load);

onMounted(async () => {
  await loadOverview(() => fetchOverview());
  if (demo.value?.business_key) store.loadHistory(demo.value.business_key);
  load();
});
</script>

<template>
  <AppShell>
    <header class="page__head reveal">
      <div>
        <p class="eyebrow">第四章 · As-of</p>
        <h1 class="page__title">时点回溯</h1>
        <p class="page__kicker">
          任意一天当时生效的客户等级与归属机构。变更按「次日生效」规则留链，所以回溯日看到的仍是当时的旧值。
        </p>
      </div>
      <div class="page__meta">
        回溯日期：{{ formatDate(asOf) }}<br />
        当时有效链：{{ store.page?.total ?? 0 }} 条
      </div>
    </header>

    <div class="page__body">
      <ErrorNotice v-if="store.error" :message="store.error" @retry="load()" />
      <ErrorNotice v-if="overviewError" :message="overviewError" @retry="loadOverview(() => fetchOverview())" />

      <PaperPanel title="时间轴" kicker="Timeline" hint="点击刻度切换回溯日期；导出的 CSV 只含当时有效链">
        <template #actions>
          <input v-model="asOf" type="date" class="input" style="width: 170px" />
          <button class="btn btn--rust btn--small" type="button" @click="exportCsv">导出时点快照 CSV</button>
        </template>
        <TimelineAxis :dates="dates" :active="asOf" clickable @pick="pick" />
        <p v-if="notice" class="note-line" style="margin-top: 10px">{{ notice }}</p>
        <p v-if="downloadError" class="form-error" style="margin-top: 10px">{{ downloadError }}</p>
      </PaperPanel>

      <div class="split" style="grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr)">
        <PaperPanel :title="`${formatDate(asOf)} 当时有效链`" kicker="As-of ledger" hint="每业务键仅一条：valid_from ≤ 回溯日 ≤ valid_to 或当前链">
          <div v-if="store.loading && !store.page" class="loading">计算时点快照…</div>
          <EmptyState
            v-else-if="!store.page || !store.page.items.length"
            title="该日期没有生效链"
            text="确认日期是否早于首个快照日 2026-11-01。"
          />
          <template v-else>
            <DimTable :rows="store.page.items" :selected-key="selectedKey" compact @select="openHistory" />
            <PaginationBar
              :page="store.page.page"
              :pages="store.page.pages"
              :total="store.page.total"
              :page-size="store.page.page_size"
              @change="pageNo = $event"
            />
          </template>
        </PaperPanel>

        <div class="stack">
          <PaperPanel title="旧值验证" kicker="Audit check" hint="2026-11-05 回溯旧等级 / 当前最新等级对照">
            <div v-if="!demoHistory" class="loading">读取 CUST-0060 编年…</div>
            <template v-else>
              <p class="small muted">{{ demoHistory.business_key }} · {{ demoHistory.versions[0]?.full_name }}</p>
              <div class="grid-stats" style="margin-top: 10px">
                <div class="stat">
                  <span class="stat__label">{{ formatDate(asOf) }} 当时</span>
                  <span class="stat__value">{{ demoAsOfRow?.customer_level || '—' }}</span>
                  <span class="stat__note">{{ demoAsOfRow ? `${formatDate(demoAsOfRow.valid_from)} 起` : '无有效链' }}</span>
                </div>
                <div class="stat">
                  <span class="stat__label">当前最新</span>
                  <span class="stat__value">{{ demoCurrentRow?.customer_level || '—' }}</span>
                  <span class="stat__note">{{ demoCurrentRow ? `${formatDate(demoCurrentRow.valid_from)} 起` : '—' }}</span>
                </div>
              </div>
              <p class="small muted" style="margin-top: 10px">
                11-05 快照观察到等级变化，按次日生效规则，新链 11-06 才开启；因此 11-05 回溯仍是旧等级。
              </p>
              <div class="row" style="margin-top: 10px">
                <StatusSeal :label="demoAsOfRow && demoCurrentRow && demoAsOfRow.customer_level !== demoCurrentRow.customer_level ? '新旧值已分离' : '同值'" :tone="demoAsOfRow && demoCurrentRow && demoAsOfRow.customer_level !== demoCurrentRow.customer_level ? 'seal--ok' : 'seal--neutral'" />
                <button class="btn btn--ghost btn--small" type="button" @click="openHistory(demoHistory.versions[demoHistory.versions.length - 1])">
                  查看完整编年
                </button>
              </div>
            </template>
          </PaperPanel>

          <PaperPanel title="回溯口径" kicker="Method">
            <ul class="small muted" style="margin: 0; padding-left: 18px; display: grid; gap: 6px">
              <li>有效期按「观察日 + 1」生效，避免夜间批处理把当天已签发保单算成新等级。</li>
              <li>当前链 valid_to 为空，任何 ≥ 生效日的回溯日都返回它。</li>
              <li>导出 CSV 含业务键、姓名、等级、机构、有效区间、版本与来源。</li>
            </ul>
          </PaperPanel>
        </div>
      </div>
    </div>

    <HistoryDrawer v-if="drawerOpen" :history="store.history" :loading="store.historyLoading" @close="drawerOpen = false" />
  </AppShell>
</template>
