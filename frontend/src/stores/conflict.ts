import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { ConflictPage, ConflictRow, ConflictSummary } from '@/types/conflict';
import * as api from '@/api/conflict';

export const useConflictStore = defineStore('conflict', () => {
  const page = ref<ConflictPage | null>(null);
  const summary = ref<ConflictSummary | null>(null);
  const status = ref<'open' | 'all'>('open');
  const loading = ref(false);
  const resolvingId = ref<number | null>(null);
  const error = ref('');
  const notice = ref('');

  async function load(pageNo = 1, pageSize = 8): Promise<void> {
    loading.value = true;
    error.value = '';
    try {
      const [list, summaryResult] = await Promise.all([
        api.fetchConflicts(status.value, pageNo, pageSize),
        api.fetchConflictSummary(),
      ]);
      page.value = list;
      summary.value = summaryResult;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载冲突队列失败';
    } finally {
      loading.value = false;
    }
  }

  async function setStatus(next: 'open' | 'all'): Promise<void> {
    status.value = next;
    await load();
  }

  async function resolve(row: ConflictRow, strategy: 'candidate' | 'manual', value: string, note: string): Promise<void> {
    resolvingId.value = row.id;
    notice.value = '';
    error.value = '';
    try {
      await api.resolveConflict(row.id, strategy, value, note);
      notice.value = `${row.business_key} · ${row.display_name} 已${strategy === 'manual' ? '人工覆盖' : '裁定'}为 ${value}，重建后按次日生效`;
      await load(page.value?.page || 1);
    } catch (err) {
      error.value = err instanceof Error ? err.message : '裁决失败';
      throw err;
    } finally {
      resolvingId.value = null;
    }
  }

  return { page, summary, status, loading, resolvingId, error, notice, load, setStatus, resolve };
});
