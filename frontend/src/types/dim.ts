import type { Paged } from './api';
import type { BuildRun } from './build';

export interface DimRow {
  business_key: string;
  version: number;
  full_name: string;
  mobile: string;
  org_code: string;
  customer_level: string;
  city: string;
  channel: string;
  valid_from: string;
  valid_to: string | null;
  is_current: boolean;
  version_source: string;
  change_fields: string[];
  attributes: Record<string, string>;
}

export interface DimPage extends Paged<DimRow> {
  run: BuildRun | null;
  level_distribution?: Record<string, number>;
  as_of?: string;
  effective_on_day?: number;
}

export interface ChainHistory {
  business_key: string;
  run: BuildRun;
  versions: DimRow[];
  conflicts: {
    id: number;
    attribute_key: string;
    snapshot_date: string;
    status: string;
    verdict: string;
    similarity: number;
    candidates: { source_code: string; value: string; canonical: string; observed_at: string; trust: number }[];
    resolution: Record<string, unknown>;
  }[];
  snapshots: {
    source_code: string;
    snapshot_date: string;
    attributes: Record<string, string>;
    ingested_at: string;
    is_late: boolean;
  }[];
}
