<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import AppShell from '@/components/common/AppShell.vue';
import PaperPanel from '@/components/common/PaperPanel.vue';
import DimTable from '@/components/common/DimTable.vue';
import HistoryDrawer from '@/components/common/HistoryDrawer.vue';
import PaginationBar from '@/components/common/PaginationBar.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import ErrorNotice from '@/components/common/ErrorNotice.vue';
import StatusSeal from '@/components/common/StatusSeal.vue';
import { useDimStore } from '@/stores/dim';
import { useDebouncedSearch } from '@/hooks/useDebouncedSearch';
import { useAsyncResource } from '@/hooks/useAsyncResource';
import { fetchOverview } from '@/api/meta';
import type { Overview } from '@/types/overview';
import type { DimRow } from '@/types/dim';
import { LEVELS, LEVEL_TONE } from '@/constants/customerLevel';
import { formatDate } from '@/utils/formatDate';

const store = useDimStore();
const router = useRouter();
const { keyword, debounced } = useDebouncedSearch('');
const level = ref('');
const pageNo = ref(1);
const selectedKey = ref('');
const drawerOpen = ref(false);
const { data: overviewData, run: loadOverview } = useAsyncResource<Overview>(null);

const distribution = computed(() => store.page?.level_distribution || {});
const totalLevels = computed(() => Object.values(distribution.value).reduce((sum, value) => sum + value, 0) || 1);

function load() {
  store.loadCurrent(debounced.value, level.value, pageNo.value, 20);
}

function openHistory(row: DimRow) {
  selectedKey.value = row.business_key;
  drawerOpen.value = true;
  store.loadHistory(row.business_key);
}

watch([debounced, level], () => {
  pageNo.value = 1;
  load();
});

watch(pageNo, load);

onMounted(async () => {
  await Promise.all([load(), loadOverview(() => fetchOverview())]);
});
</script>

<template>
  <AppShell>
    <header class="page__head reveal">
      <div>
        <p class="eyebrow">第三章 · Current</p>
        <h1 class="page__title">当前维度浏览</h1>
        <p class="page__kicker">
          最新成功批次里的 180 条当前链。点开任意客户，可以看到它每一段「当时等级」的起止与变更字段。
        </p>
      </div>
      <div class="page__meta">
        批次：
        <template v-if="store.page?.run">#{{ store.page.run.run_no }} · {{ formatDate(store.page.run.as_of_cutoff) }}</template>
        <template v-else>—</template>
        <br />
        当前链：{{ store.page?.total ?? 0 }} / {{ overviewData?.current_customers ?? 180 }}
      </div>
    </header>

    <div class="page__body">
      <ErrorNotice v-if="store.error" :message="store.error" @retry="load()" />

      <div class="split split--browse">
        <PaperPanel title="当前链台账" kicker="Chronicle ledger" hint="业务键 / 姓名 / 等级 / 归属机构 / 生效区间">
          <template #actions>
            <StatusSeal label="只读浏览" tone="seal--neutral" />
          </template>
          <div class="toolbar" style="margin-bottom: 12px">
            <div class="field toolbar__grow">
              <span class="field__label">搜索业务键 / 姓名 / 机构</span>
              <input v-model="keyword" class="input" placeholder="CUST-0060 / 陈嘉禾 / BJ01" />
            </div>
            <div class="field">
              <span class="field__label">等级</span>
              <select v-model="level" class="select" style="min-width: 130px">
                <option value="">全部等级</option>
                <option v-for="item in LEVELS" :key="item" :value="item">{{ item }}</option>
              </select>
            </div>
          </div>

          <div v-if="store.loading && !store.page" class="loading">读取当前维度…</div>
          <EmptyState
            v-else-if="!store.page || !store.page.items.length"
            title="没有匹配的客户"
            text="试试清空关键词，或去构建运行页确认最新批次是否成功。"
          >
            <button class="btn btn--small" style="margin-top: 10px" type="button" @click="keyword = ''; level = ''; load()">清空筛选</button>
          </EmptyState>
          <template v-else>
            <DimTable :rows="store.page.items" :selected-key="selectedKey" @select="openHistory" />
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
          <PaperPanel title="等级分布" kicker="Level census" hint="当前链按客户等级计数">
            <div v-if="!Object.keys(distribution).length" class="loading">暂无分布数据</div>
            <div v-else class="stack" style="gap: 10px">
              <div v-for="item in LEVELS" :key="item">
                <div class="spread small">
                  <span>{{ item }}</span>
                  <span class="numeral">{{ distribution[item] || 0 }} 人</span>
                </div>
                <div class="check-bar" style="margin-top: 4px">
                  <div class="check-bar__fill" :style="{ width: `${Math.round(((distribution[item] || 0) / totalLevels) * 100)}%` }" />
                </div>
              </div>
              <p class="small muted" style="margin-top: 6px">
                钻卡 / 白金客户等级变更直接影响监管报送口径，变更必须留链。
              </p>
            </div>
          </PaperPanel>

          <PaperPanel title="编年提示" kicker="Reading note">
            <div class="stack" style="gap: 10px">
              <p class="small">
                2026-11-05 的时点回溯里，<strong>CUST-0060 罗欣悦</strong> 当时仍是「银卡」——
                它在 11-05 的快照里被观察到升级，按次日生效规则，新链从 11-06 才开始。
              </p>
              <p class="small muted">
                想验证这一点，去「时点回溯」页把日期停在 2026-11-05，再和本页当前值对照。
              </p>
              <div class="row">
                <button class="btn btn--small" type="button" @click="router.push('/dims/as-of')">去时点回溯</button>
                <button class="btn btn--ghost btn--small" type="button" @click="router.push('/builds')">看构建批次</button>
              </div>
              <div class="legend">
                <span><i class="is-current" />当前链</span>
                <span><i class="is-manual" />人工覆盖</span>
                <span><i class="is-closed" />已关链</span>
              </div>
            </div>
          </PaperPanel>

          <PaperPanel title="等级口径" kicker="Scale">
            <div class="chips">
              <span v-for="item in LEVELS" :key="item" class="chip">
                <StatusSeal :label="item" :tone="LEVEL_TONE[item]" />
              </span>
            </div>
            <p class="small muted" style="margin-top: 10px">
              银卡 → 金卡 → 白金卡 → 钻石卡；等级下调同样开新链，不覆盖旧链。
            </p>
          </PaperPanel>
        </div>
      </div>
    </div>

    <HistoryDrawer
      v-if="drawerOpen"
      :history="store.history"
      :loading="store.historyLoading"
      @close="drawerOpen = false"
    />
  </AppShell>
</template>
