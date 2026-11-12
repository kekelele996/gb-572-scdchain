import { request } from '@/utils/request';
import type { BuildRun, CompareResult } from '@/types/build';

export function fetchRuns(limit = 20) {
  return request<{ items: BuildRun[] }>(`/builds?limit=${limit}`);
}

export function fetchRun(runId: number) {
  return request<BuildRun>(`/builds/${runId}`);
}

export function createRun(notes: string) {
  return request<BuildRun>('/builds', { method: 'POST', body: { notes } });
}

export function fetchCompare(leftId: number, rightId: number) {
  return request<CompareResult>(`/builds/compare?left_id=${leftId}&right_id=${rightId}`);
}
