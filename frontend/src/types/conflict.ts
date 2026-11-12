import type { Paged } from './api';

export interface ConflictCandidate {
  source_code: string;
  source_name?: string;
  value: string;
  canonical: string;
  observed_at: string;
  trust: number;
}

export interface ConflictRow {
  id: number;
  business_key: string;
  attribute_key: string;
  display_name: string;
  normalization: string;
  snapshot_date: string;
  candidates: ConflictCandidate[];
  verdict: 'normalized_equal' | 'similar' | 'conflict';
  verdict_label: string;
  similarity: number;
  status: 'open' | 'resolved' | 'manual';
  status_label: string;
  resolution: Record<string, string | number | undefined>;
  strategy_label: string;
  resolved_by: string;
  resolved_at: string | null;
  effective_date: string | null;
}

export type ConflictPage = Paged<ConflictRow>;

export interface ConflictSummary {
  total: number;
  open: number;
  by_status: Record<string, number>;
  by_verdict: Record<string, number>;
  by_strategy: Record<string, number>;
  labels: {
    status: Record<string, string>;
    strategy: Record<string, string>;
    verdict: Record<string, string>;
  };
}
