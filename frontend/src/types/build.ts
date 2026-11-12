import type { Invariants } from './api';

export interface RunStats {
  snapshots_used: number;
  customers: number;
  chains_total: number;
  chains_closed: number;
  changed_keys: number;
  changes: number;
  late_arrivals: number;
  collapsed_same_day: number;
  overrides_applied: number;
  ignored_columns: string[];
  conflicts_detected: number;
  conflicts_auto_resolved: number;
  conflicts_open: number;
  snapshot_dates: string[];
  as_of_cutoff: string | null;
  previous_run_id: number | null;
  new_chains: number;
  removed_chains: number;
  changed_versions?: number;
}

export interface BuildRun {
  id: number;
  run_no: number;
  label: string;
  mode: string;
  status: 'pending' | 'running' | 'succeeded' | 'failed';
  triggered_by: string;
  as_of_cutoff: string | null;
  started_at: string | null;
  finished_at: string | null;
  stats: RunStats;
  invariants: Invariants;
  input_hash: string;
  previous_run_id: number | null;
  notes: string;
  error_message: string;
  previous?: BuildRun | null;
  chain_samples?: ChainSample[];
}

export interface ChainSample {
  business_key: string;
  valid_from: string;
  valid_to: string | null;
  version: number;
  version_source: string;
  change_fields: string[];
  attributes: Record<string, string>;
}

export interface CompareResult {
  left: BuildRun;
  right: BuildRun;
  new_chains: number;
  removed_chains: number;
  changed_versions: number;
  changed_keys: number;
  new_chain_samples: ChainSample[];
  removed_chain_samples: ChainSample[];
  current_change_samples: {
    business_key: string;
    left: Record<string, string>;
    right: Record<string, string>;
    right_valid_from: string;
    version_source: string;
  }[];
}
