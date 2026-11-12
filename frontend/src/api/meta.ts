import { request } from '@/utils/request';
import type { Overview } from '@/types/overview';
import type { Paged } from '@/types/api';

export function fetchOverview() {
  return request<Overview>('/meta/overview');
}

export function fetchAuditLogs(limit = 100) {
  return request<Paged<{ id: number; actor_email: string; actor_role: string; action: string; resource_type: string; resource_id: string; detail: Record<string, unknown>; created_at: string }>>(
    `/audit-logs?limit=${limit}`,
  );
}
