import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { BuildRun, CompareResult } from '@/types/build';
import * as api from '@/api/build';
import { sleep } from '@/utils/sleep';

export const useBuildStore = defineStore('build', () => {
  const runs = ref<BuildRun[]>([]);
  const selectedId = ref<number | null>(null);
  const detail = ref<BuildRun | null>(null);
  const compare = ref<CompareResult | null>(null);
  const loading = ref(false);
  const creating = ref(false);
  const error = ref('');

  const selected = computed(() => runs.value.find((run) => run.id === selectedId.value) || detail.value || null);
  const succeededRuns = computed(() => runs.value.filter((run) => run.status === 'succeeded'));

  async function loadRuns(): Promise<void> {
    loading.value = true;
    error.value = '';
    try {
      runs.value = (await api.fetchRuns(20)).items;
      if (!selectedId.value && runs.value.length) selectedId.value = runs.value[0].id;
      if (selectedId.value) await loadDetail(selectedId.value);
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载构建批次失败';
    } finally {
      loading.value = false;
    }
  }

  async function loadDetail(runId: number): Promise<void> {
    selectedId.value = runId;
    detail.value = await api.fetchRun(runId);
  }

  async function select(runId: number): Promise<void> {
    compare.value = null;
    await loadDetail(runId);
  }

  async function loadCompare(leftId: number, rightId: number): Promise<void> {
    compare.value = await api.fetchCompare(leftId, rightId);
  }

  async function create(notes: string): Promise<BuildRun> {
    creating.value = true;
    try {
      const run = await api.createRun(notes);
      runs.value = [run, ...runs.value];
      selectedId.value = run.id;
      return run;
    } finally {
      creating.value = false;
    }
  }

  async function pollUntilDone(runId: number, timeoutMs = 60_000): Promise<BuildRun> {
    const started = Date.now();
    for (;;) {
      const run = await api.fetchRun(runId);
      detail.value = run;
      runs.value = runs.value.map((item) => (item.id === run.id ? run : item));
      if (run.status === 'succeeded' || run.status === 'failed') return run;
      if (Date.now() - started > timeoutMs) return run;
      await sleep(900);
    }
  }

  return { runs, selectedId, selected, detail, compare, loading, creating, error, succeededRuns, loadRuns, select, loadCompare, create, pollUntilDone };
});
