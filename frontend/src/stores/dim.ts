import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { ChainHistory, DimPage, DimRow } from '@/types/dim';
import * as api from '@/api/dim';

export const useDimStore = defineStore('dim', () => {
  const page = ref<DimPage | null>(null);
  const history = ref<ChainHistory | null>(null);
  const historyLoading = ref(false);
  const loading = ref(false);
  const error = ref('');
  const selectedKey = ref('');

  async function loadCurrent(search = '', level = '', pageNo = 1, pageSize = 20): Promise<void> {
    await wrap(() => api.fetchCurrentDims({ search, level, page: pageNo, pageSize }));
  }

  async function loadAsOf(asOf: string, search = '', level = '', pageNo = 1, pageSize = 20): Promise<void> {
    await wrap(() => api.fetchAsOfDims(asOf, { search, level, page: pageNo, pageSize }));
  }

  async function wrap(task: () => Promise<DimPage>): Promise<void> {
    loading.value = true;
    error.value = '';
    try {
      page.value = await task();
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载维度失败';
    } finally {
      loading.value = false;
    }
  }

  async function loadHistory(businessKey: string): Promise<void> {
    selectedKey.value = businessKey;
    historyLoading.value = true;
    try {
      history.value = await api.fetchHistory(businessKey);
    } catch (err) {
      history.value = null;
      error.value = err instanceof Error ? err.message : '加载编年条目失败';
    } finally {
      historyLoading.value = false;
    }
  }

  function selectedRow(): DimRow | null {
    if (!history.value) return null;
    return history.value.versions[history.value.versions.length - 1] || null;
  }

  return { page, history, historyLoading, loading, error, selectedKey, loadCurrent, loadAsOf, loadHistory, selectedRow };
});
