import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { MergeRule, RuleUpdatePayload, SnapshotFeed, SourceSystem } from '@/types/dimension';
import * as api from '@/api/dimension';

export const useDimensionStore = defineStore('dimension', () => {
  const rules = ref<MergeRule[]>([]);
  const sources = ref<SourceSystem[]>([]);
  const feed = ref<SnapshotFeed | null>(null);
  const loading = ref(false);
  const savingId = ref<number | null>(null);
  const error = ref('');

  async function load(): Promise<void> {
    loading.value = true;
    error.value = '';
    try {
      const [ruleResult, feedResult] = await Promise.all([api.fetchRules(), api.fetchSnapshotFeed(16)]);
      rules.value = ruleResult.items;
      sources.value = ruleResult.sources;
      feed.value = feedResult;
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载维度设计失败';
    } finally {
      loading.value = false;
    }
  }

  async function save(ruleId: number, payload: RuleUpdatePayload): Promise<MergeRule> {
    savingId.value = ruleId;
    try {
      const updated = await api.updateRule(ruleId, payload);
      rules.value = rules.value.map((rule) => (rule.id === ruleId ? updated : rule));
      return updated;
    } finally {
      savingId.value = null;
    }
  }

  return { rules, sources, feed, loading, savingId, error, load, save };
});
