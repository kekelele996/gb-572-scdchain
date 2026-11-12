import { request } from '@/utils/request';
import type { ChainHistory, DimPage } from '@/types/dim';

interface DimQuery {
  search?: string;
  level?: string;
  page?: number;
  pageSize?: number;
}

function queryString(query: DimQuery): string {
  const params = new URLSearchParams();
  if (query.search) params.set('search', query.search);
  if (query.level) params.set('level', query.level);
  params.set('page', String(query.page || 1));
  params.set('page_size', String(query.pageSize || 20));
  return params.toString();
}

export function fetchCurrentDims(query: DimQuery = {}) {
  return request<DimPage>(`/dims/current?${queryString(query)}`);
}

export function fetchAsOfDims(asOf: string, query: DimQuery = {}) {
  return request<DimPage>(`/dims/as-of?as_of=${encodeURIComponent(asOf)}&${queryString(query)}`);
}

export function fetchHistory(businessKey: string) {
  return request<ChainHistory>(`/dims/${encodeURIComponent(businessKey)}/history`);
}

export function fetchAttributes() {
  return request<{ items: { key: string; label: string; data_type: string; enum_values: string[]; description: string; default_normalization: string }[] }>(
    '/dims/attributes',
  );
}
