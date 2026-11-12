import type { BuildRun } from './build';
import type { ConflictSummary } from './conflict';
import type { SourceSystem } from './dimension';

export interface Overview {
  brand: string;
  snapshot_rows: number;
  snapshot_dates: string[];
  latest_run: BuildRun | null;
  current_customers: number;
  level_distribution: Record<string, number>;
  conflicts: {
    by_status: Record<string, number>;
    by_strategy: Record<string, number>;
    open: number;
    total: number;
  };
  asof_demo: { business_key: string; as_of: string };
  strategy_labels: Record<string, string>;
  sources: SourceSystem[];
  runs: BuildRun[];
  conflict_summary: ConflictSummary;
}
