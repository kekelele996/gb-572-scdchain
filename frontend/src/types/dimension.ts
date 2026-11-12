export interface MergeRule {
  id: number;
  attribute_key: string;
  display_name: string;
  data_type: string;
  source_priority: string[];
  normalization: string;
  exclude_from_change: boolean;
  description: string;
  updated_by: string;
  updated_at: string | null;
  enum_values: string[];
  priority_sources: { code: string; name: string }[];
}

export interface SourceSystem {
  id: number;
  code: string;
  name: string;
  system_type: string;
  description: string;
  contact_owner: string;
  snapshot_time: string;
  trust_level: number;
  is_active: boolean;
}

export interface SnapshotBatch {
  snapshot_date: string;
  source_code: string;
  rows: number;
  late_rows: number;
}

export interface SnapshotFeed {
  summary: { total_rows: number; snapshot_dates: string[]; batches: SnapshotBatch[] };
  rows: {
    id: number;
    source_code: string;
    source_name: string;
    business_key: string;
    snapshot_date: string;
    attributes: Record<string, string>;
    ingested_at: string;
    is_late: boolean;
    batch_tag: string;
  }[];
}

export interface RuleUpdatePayload {
  source_priority?: string[];
  normalization?: string;
  exclude_from_change?: boolean;
  description?: string;
}
