import { request } from '@/utils/request';
import type { ConflictPage, ConflictRow, ConflictSummary } from '@/types/conflict';

export function fetchConflicts(status = 'all', page = 1, pageSize = 10) {
  return request<ConflictPage>(`/conflicts?status=${encodeURIComponent(status)}&page=${page}&page_size=${pageSize}`);
}

export function fetchConflictSummary() {
  return request<ConflictSummary>('/conflicts/summary');
}

export function resolveConflict(conflictId: number, strategy: 'candidate' | 'manual', value: string, note: string) {
  return request<ConflictRow>(`/conflicts/${conflictId}/resolve`, {
    method: 'POST',
    body: { strategy, value, note },
  });
}
