import { request } from '@/utils/request';
import type { MergeRule, RuleUpdatePayload, SnapshotFeed, SourceSystem } from '@/types/dimension';

export function fetchRules() {
  return request<{ items: MergeRule[]; sources: SourceSystem[] }>('/dimensions/rules');
}

export function updateRule(ruleId: number, payload: RuleUpdatePayload) {
  return request<MergeRule>(`/dimensions/rules/${ruleId}`, { method: 'PUT', body: payload });
}

export function fetchSnapshotFeed(limit = 12) {
  return request<SnapshotFeed>(`/snapshots/feed?limit=${limit}`);
}
